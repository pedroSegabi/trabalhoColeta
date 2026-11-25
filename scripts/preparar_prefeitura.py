"""Bases da Prefeitura de Porto Alegre (dadosabertos.poa.br) usadas no dashboard.

- Malha oficial de bairros (Lei Complementar 12.112/2016) -> mapa coroplético da Tela 1
- Cadastro de escolas da rede municipal e conveniada (SMED) -> escolas x nível do rio (Tela 2)

Coleta responsável: o robots.txt do portal bloqueia /api/ e pede Crawl-Delay de 10 s; usamos só os
links públicos de download e esperamos o tempo pedido (ver baixar() em coletar_ibge.py).

Uso:  python scripts/preparar_prefeitura.py   (depois de limpar_inct.py)
Saída: dados/processados/bairros_poa.geojson (94 bairros, WGS84, nomes iguais aos do INCT)
       dados/processados/escolas_poa.csv     (uma linha por escola, com o bairro no padrão do INCT)
"""
import json
import unicodedata

import geopandas as gpd
import pandas as pd

from coletar_ibge import PROC, baixar

DOWNLOAD = "https://dadosabertos.poa.br/dataset/{}/resource/{}/download/{}"
BAIRROS = ("bairros_lc12112_16.zip", DOWNLOAD.format(
    "a7172700-e0e2-4797-bf4a-12f658828568", "1de9991b-ae77-4359-a0cc-daf82fdf1896", "bairros_lc12112_16.zip"))
ESCOLAS = ("cadastro_escolas.csv", DOWNLOAD.format(
    "5d204437-8335-43d5-8df3-102a35fc97fb", "5579bc8e-1e47-47ef-a06e-9f08da28dec8", "cadastro_escolas.csv"))

# Grafias da Prefeitura que não batem com o INCT mesmo depois de normalizar (abreviadas ou truncadas)
APELIDOS = {
    "CEL APARICIO BORGES": "CORONEL APARICIO BORGES",
    "CORONEL APARICIO BOR": "CORONEL APARICIO BORGES",
    "PASSO DA AREIA": "PASSO DAREIA",
    "ABERTA MORROS": "ABERTA DOS MORROS",
    "CENTRO HISTORIC": "CENTRO HISTORICO",
    "PASSO DAS PEDRA": "PASSO DAS PEDRAS",
    "VL JOAO PESSOA": "VILA JOAO PESSOA",
}


def chave(nome):
    """Forma comparável de um nome de bairro: sem acento, maiúscula, sem apóstrofo/ponto, espaços simples."""
    s = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    s = " ".join(s.upper().replace("'", "").replace(".", " ").split())
    return APELIDOS.get(s, s)


def bairros(inct):
    arquivo, _ = baixar(*BAIRROS)
    g = gpd.read_file(arquivo)  # shapefile em TM-POA (SIRGAS 2000), em metros
    g["bairro"] = g["NOME"].map(chave).map(inct)
    assert g["bairro"].notna().all(), sorted(g.loc[g["bairro"].isna(), "NOME"].unique())
    g = g.dissolve("bairro", as_index=False)[["bairro", "geometry"]]  # 128 polígonos -> 94 bairros (ilhas juntas)
    assert sorted(g["bairro"]) == sorted(inct.values())  # os 94 bairros do INCT, nem mais nem menos
    # Simplifica (tolerância de 10 m) e arredonda para 5 casas decimais (~1 m): 3,4 MB -> ~175 KB,
    # diferença invisível num mapa da cidade inteira
    leve = g.assign(geometry=g.simplify(10)).to_crs(4326)
    leve["geometry"] = leve.set_precision(1e-5)
    saida = PROC / "bairros_poa.geojson"
    saida.write_text(leve.to_json(drop_id=True, to_wgs84=True))
    print(f"ok: {saida.name} -> {len(leve)} bairros ({saida.stat().st_size / 1024:.0f} KB)")
    return g  # em metros, para o cruzamento espacial das escolas


def escolas(inct, malha):
    arquivo, _ = baixar(*ESCOLAS)
    consertadas = []

    def consertar(campos):
        # 3 linhas têm 42 campos em vez de 40: ';' dentro do e-mail/site, que vêm DEPOIS da coluna bairro.
        # Os 31 primeiros campos e os 9 últimos estão no lugar certo; só as colunas de site/redes se perdem.
        consertadas.append(campos[24].strip())
        return campos[:31] + campos[-9:]

    e = pd.read_csv(arquivo, sep=";", dtype=str, engine="python", on_bad_lines=consertar)
    e = e.apply(lambda c: c.str.strip())
    print(f"{len(consertadas)} linhas com campos a mais recuperadas: {consertadas}")

    e["bairro_inct"] = e["bairro"].map(chave).map(inct)
    assert e["bairro_inct"].notna().all(), sorted(e.loc[e["bairro_inct"].isna(), "bairro"].unique())

    # Conferência espacial. As colunas "latitude"/"longitude" do cadastro são, na verdade, X/Y em TM-POA
    # (metros, rótulos trocados). O ponto de cada escola deve cair no bairro declarado.
    pontos = gpd.GeoDataFrame(e, crs=malha.crs, geometry=gpd.points_from_xy(
        e["latitude"].astype(float), e["longitude"].astype(float)))
    no_mapa = gpd.sjoin(pontos, malha.rename(columns={"bairro": "bairro_mapa"}), predicate="within", how="left")
    e["bairro_mapa"] = no_mapa.groupby(level=0)["bairro_mapa"].first()
    sem_ponto = e["latitude"].astype(float).eq(0)  # coordenada (0, 0) = escola sem localização
    assert e.loc[~sem_ponto, "bairro_mapa"].notna().all()  # toda escola com coordenada cai em algum bairro
    diferente = ~sem_ponto & (e["bairro_mapa"] != e["bairro_inct"])
    print(f"{sem_ponto.sum()} escolas sem coordenada; {diferente.sum()} com bairro declarado diferente do ponto, "
          "quase sempre a divisão anterior à lei de 2016. Ex.:")
    print(e.loc[diferente, ["bairro_inct", "bairro_mapa"]].value_counts().head(8).to_string())

    # Vale o bairro do ponto (mesma divisão de 2016 usada pelo INCT); sem coordenada, o bairro declarado
    e["bairro"] = e["bairro_mapa"].where(~sem_ponto, e["bairro_inct"])
    e["origem_bairro"] = ["cadastro (sem coordenada)" if s else "ponto na malha oficial" for s in sem_ponto]
    e["rede"] = e["dep_administrativa"].map({"MUNICIPAL": "Municipal", "PRIVADO": "Conveniada"})
    assert e["rede"].notna().all() and e["bairro"].notna().all()
    saida = PROC / "escolas_poa.csv"
    e.rename(columns={"nome": "escola", "bairro_inct": "bairro_cadastro"})[
        ["escola", "rede", "tipo", "bairro", "origem_bairro", "bairro_cadastro", "data_extracao"]
    ].to_csv(saida, index=False)
    print(f"ok: {saida.name} -> {len(e)} escolas ({e['rede'].value_counts().to_dict()})")


def main():
    nomes = {r["bairro"] for r in json.loads((PROC / "inct_limpo.json").read_text(encoding="utf-8"))}
    inct = {chave(n): n for n in nomes}
    assert len(inct) == 94  # a normalização não junta dois bairros diferentes
    malha = bairros(inct)
    escolas(inct, malha)


if __name__ == "__main__":
    main()
