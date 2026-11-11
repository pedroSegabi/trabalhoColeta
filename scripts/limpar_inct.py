"""Limpeza do data.json do INCT SiMAI (Tela 1).

Uso:  python scripts/limpar_inct.py
Saída: dados/processados/inct_limpo.json   (formato longo: uma linha por nível x bairro)
       dados/processados/inct_correcoes.csv (cada valor alterado, com método e motivo)

Regra física usada para achar erros: quando o rio sobe, o número de prédios afetados
de um bairro nunca pode diminuir (a água que alaga a 5 m continua lá a 6 m).
"""
import json
import math
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
ENTRADA = RAIZ / "dados" / "originais" / "data.json"
PROC = RAIZ / "dados" / "processados"

# Correções pontuais decididas após inspecionar as séries (ver relatorios/limpeza_dados.pdf).
# (bairro, níveis, motivo). Os valores viram NaN e são reconstruídos pelos vizinhos.
CORRECOES = [
    ("Centro Histórico", [9.7, 9.8], "zero isolado entre 2050 (9,6 m) e 2130 (9,9 m)"),
    ("Lageado", [8.1], "zero isolado entre 108 (8,0 m) e 110 (8,2 m)"),
    ("Rubem Berta", [8.8], "zero isolado entre 252 (8,7 m) e 285 (8,9 m)"),
    ("Espírito Santo", [4.7], "pico isolado de 2101 entre 46 (4,6 m) e 47 (4,8 m)"),
    ("Espírito Santo", [3.0, 3.1, 3.2, 3.3, 3.4], "637/633 prédios, mais do que o bairro tem a 10 m (133)"),
]


def carregar():
    """Código mínimo do enunciado: lê por chave, então ordem de níveis/bairros/campos não importa."""
    with open(ENTRADA, encoding="utf-8") as f:
        raw = json.load(f)
    df = pd.DataFrame([
        {"nivel_m": float(nivel.removesuffix("m").replace("_", ".")), "bairro": bairro, **valores}
        for nivel, bairros in raw.items()
        for bairro, valores in bairros.items()
    ])
    return raw, df


def validar_estrutura(raw, df):
    assert df.shape == (6674, 7), df.shape
    assert set(df["nivel_m"].round(1)) == {round(3 + i / 10, 1) for i in range(71)}  # 3,0..10,0 m, passo 0,1
    assert df["bairro"].nunique() == 94  # pega grafias diferentes do mesmo bairro entre níveis
    assert df.groupby("nivel_m")["bairro"].nunique().eq(94).all()
    campos = ["affected_buildings", "total_buildings", "percentage", "population", "affected_population"]
    assert (df[campos].dtypes == "int64").all()
    assert not df.duplicated(["nivel_m", "bairro"]).any()
    assert df.notna().all().all()
    # total de prédios e população são atributos do bairro: não podem mudar com o nível
    assert df.groupby("bairro")[["total_buildings", "population"]].nunique().eq(1).all().all()
    assert df.groupby("nivel_m")["population"].sum().eq(1332845).all()  # = Censo 2022 de POA

    # Achado estrutural: níveis com campos em outra ordem (sinal de lotes diferentes)
    outra_ordem = [k for k, b in raw.items() if next(iter(next(iter(b.values())))) == "affected_buildings"]
    ref = list(raw["3_0m"])
    outra_ordem_bairros = [k for k, b in raw.items() if list(b) != ref]
    print(f"níveis com 'affected_buildings' como 1º campo: {outra_ordem}")
    print(f"níveis com bairros em outra ordem: {outra_ordem_bairros}")


def quedas(df, col="affected_buildings"):
    """Linhas em que o valor diminui em relação ao nível anterior do mesmo bairro."""
    d = df.sort_values(["bairro", "nivel_m"])
    anterior = d.groupby("bairro")[col].shift()
    return d.assign(anterior=anterior)[d[col] < anterior]


def diagnosticar_calculos(df):
    # (a/t)*100 em ponto flutuante, como o INCT aparentemente calculou: 686/2450*100 = 28.000000000000004
    teto_float = (df["affected_buildings"] / df["total_buildings"] * 100).apply(math.ceil)
    teto_exato = (100 * df["affected_buildings"] / df["total_buildings"]).apply(math.ceil)
    print(f"percentage == teto((a/t)*100) em {(df['percentage'] == teto_float).sum()} de {len(df)} linhas")
    artefato = df[teto_float != teto_exato]
    print("linhas em que o erro de ponto flutuante muda o teto (deveria ser o valor exato):")
    print(artefato[["nivel_m", "bairro", "affected_buildings", "total_buildings", "percentage"]].to_string(index=False))
    pop_teto = (df["population"] * df["percentage"] / 100).apply(math.ceil)
    print(f"affected_population == teto(pop*pct/100) em {(df['affected_population'] == pop_teto).sum()} linhas")


def limpar(df):
    df = df.sort_values(["bairro", "nivel_m"]).reset_index(drop=True)
    for c in ["affected_buildings", "percentage", "affected_population"]:
        df[f"{c}_orig"] = df[c]
    df["correcao"] = ""

    # 1) erros pontuais -> NaN -> interpolação linear entre vizinhos (ou valor seguinte no início da série)
    a = df["affected_buildings"].astype(float)
    for bairro, niveis, _ in CORRECOES:
        alvo = (df["bairro"] == bairro) & df["nivel_m"].round(1).isin(niveis)
        assert alvo.sum() == len(niveis), (bairro, niveis)
        a[alvo] = float("nan")
    a = a.groupby(df["bairro"]).transform(lambda s: s.interpolate().bfill()).round()
    mudou = a != df["affected_buildings"]
    df.loc[mudou, "correcao"] = "interpolado"
    inicio_es = (df["bairro"] == "Espírito Santo") & (df["nivel_m"] < 3.45)
    df.loc[inicio_es, "correcao"] = "preenchido com o valor de 3,5 m"

    # 2) Arquipélago oscila em torno de 4680 (valor de 64 dos 71 níveis); os desvios caem nos níveis
    #    do lote com estrutura diferente (3,0/3,5/4,0/4,5/5,0/5,3 m) e em 4,1 m -> usa o valor modal
    arq = df["bairro"] == "Arquipélago"
    moda = a[arq].mode()[0]
    df.loc[arq & (a != moda), "correcao"] = "valor modal do bairro"
    a[arq] = moda
    df["affected_buildings"] = a.astype("int64")

    # 3) recalcula os campos derivados sem arredondar para cima
    frac = df["affected_buildings"] / df["total_buildings"]
    df["percentage"] = (100 * frac).round(2)
    df["affected_population"] = (df["population"] * frac).round().astype("int64")
    return df


def validar_limpo(df):
    assert len(quedas(df)) == 0
    assert df["percentage"].between(0, 100).all()
    assert (df["affected_buildings"] <= df["total_buildings"]).all()
    assert (df["affected_population"] <= df["population"]).all()


def main():
    raw, df = carregar()
    validar_estrutura(raw, df)

    q = quedas(df)
    print(f"\n{len(q)} quedas de prédios afetados quando o rio sobe:")
    print(q[["bairro", "nivel_m", "anterior", "affected_buildings"]].to_string(index=False))
    print()
    diagnosticar_calculos(df)

    limpo = limpar(df)
    validar_limpo(limpo)

    corr = limpo[limpo["correcao"] != ""]
    motivo = {(b, n): m for b, ns, m in CORRECOES for n in ns}
    corr = corr.assign(motivo=[motivo.get((b, round(n, 1)), "oscilação de até 14 prédios num bairro 100% alagado; "
                                          "usado o valor de 64 dos 71 níveis (4680)")
                               for b, n in zip(corr["bairro"], corr["nivel_m"])])
    corr[["bairro", "nivel_m", "affected_buildings_orig", "affected_buildings", "correcao", "motivo"]] \
        .to_csv(PROC / "inct_correcoes.csv", index=False)

    colunas = ["nivel_m", "bairro", "affected_buildings", "total_buildings", "percentage",
               "population", "affected_population", "affected_buildings_orig",
               "percentage_orig", "affected_population_orig", "correcao"]
    limpo = limpo.sort_values(["nivel_m", "bairro"])[colunas]
    limpo.to_json(PROC / "inct_limpo.json", orient="records", force_ascii=False, indent=1)

    print(f"\n{len(corr)} valores de affected_buildings alterados -> dados/processados/inct_correcoes.csv")
    tot = limpo.groupby("nivel_m")[["affected_population_orig", "affected_population"]].sum()
    tot["diferenca"] = tot["affected_population_orig"] - tot["affected_population"]
    print("\npopulação afetada na cidade (original x limpo):")
    print(tot.loc[[3.0, 4.0, 4.7, 5.0, 5.3, 5.4, 6.0, 8.0, 9.7, 10.0]].to_string())
    print(f"\nok: dados/processados/inct_limpo.json -> {limpo.shape}")


if __name__ == "__main__":
    main()
