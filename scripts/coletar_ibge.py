"""Coleta e preparação da base externa da Tela 2.

Fonte: IBGE - "Dados agregados para as áreas afetadas - Municípios do RS".
O IBGE cruzou o Censo 2022 / CNEFE com duas manchas de inundação de 2024:
  - SPGG-RS (15/05/2024): mancha da Secretaria de Planejamento do RS, a mesma usada
    no Mapa Único do Plano Rio Grande (MUP, mup.rs.gov.br). O MUP é um painel
    Power BI sem download/API, então usamos esta agregação oficial publicada em xlsx.
  - v3 INPE/ANA (19/06/2024): mancha final do grupo de trabalho federal.

Também baixa a malha municipal do RS (API de malhas do IBGE) usada no mapa da Tela 2.

Uso:  python scripts/coletar_ibge.py
Saída: dados/originais/ibge_*.xlsx e ibge_malha_rs_municipios.geojson (brutos, baixados só uma vez)
       dados/originais/coleta.json (URL e data de coleta de cada arquivo)
       dados/processados/ibge_areas_afetadas.csv (formato longo: município x mancha)
"""
import datetime as dt
import json
import time
import urllib.parse
import urllib.robotparser
from pathlib import Path

import pandas as pd
import requests

RAIZ = Path(__file__).resolve().parents[1]
ORIG = RAIZ / "dados" / "originais"
PROC = RAIZ / "dados" / "processados"

FTP = "https://ftp.ibge.gov.br/Informacoes_Gerais_e_Referencia/SINGED_Lab/apoio_rs/"
FONTES = {
    "spgg_mup_15mai24": (
        "ibge_areas_afetadas_spgg_15mai24.xlsx",
        FTP + "Solicitacoes_especiais/08_Secretaria_de_Plan_Gov_e_Gestao_do_RS/"
        "Dados%20Agregados%20para%20as%20%C3%81reas%20Afetadas%20-%20Munic%C3%ADpios"
        "%20do%20RS%20-%20SPGG-RS%20-%2015mai24.xlsx",
    ),
    "inpe_ana_v3_19jun24": (
        "ibge_areas_afetadas_v3_26jun24.xlsx",
        FTP + "Dados_agregados_para_toda_a_area_afetada_v3_Governo_Federal/"
        "Dados_Agregados_para_as_Areas_Afetadas_Municipios_do_RS_GTCasaCivil_26jun24.xlsx",
    ),
}

# Colunas C..K = área afetada, L..T = total do município (U..AC = % é recalculado aqui)
INDICADORES = [
    "pessoas", "domicilios_particulares", "domicilios_coletivos", "edificacoes_construcao",
    "estab_agropecuarios", "estab_ensino", "estab_saude", "estab_religiosos", "estab_outros",
]


# Malha municipal do RS (polígonos simplificados, WGS84) para o mapa da Tela 2; "codarea" = cod_ibge
MALHA_RS = ("ibge_malha_rs_municipios.geojson",
            "https://servicodados.ibge.gov.br/api/v3/malhas/estados/43"
            "?formato=application/vnd.geo+json&qualidade=minima&intrarregiao=municipio")

REGISTRO = ORIG / "coleta.json"  # URL e data de download de cada arquivo (o git não guarda a data)
HEADERS = {"User-Agent": "projeto-academico-enchentes"}


def robots(url):
    """Consulta o robots.txt do site da URL: (pode baixar?, segundos de espera pedidos pelo site)."""
    site = urllib.parse.urlsplit(url)
    try:
        resp = requests.get(f"{site.scheme}://{site.netloc}/robots.txt", timeout=15, headers=HEADERS)
    except requests.Timeout:
        # servicodados.ibge.gov.br (API pública e documentada do IBGE) não responde em /robots.txt
        print(f"aviso: {site.netloc}/robots.txt não respondeu; tratado como inexistente")
        return True, 0
    if resp.status_code in (404, 410):  # sem robots.txt -> sem restrições (ftp.ibge.gov.br hoje é 404)
        return True, 0
    resp.raise_for_status()  # 401/403/429/5xx: não presume permissão
    regras = urllib.robotparser.RobotFileParser()
    regras.parse(resp.text.splitlines())
    return regras.can_fetch(HEADERS["User-Agent"], url), regras.crawl_delay(HEADERS["User-Agent"]) or 0


def baixar(nome, url):
    """Baixa o arquivo só se ainda não existe localmente (coleta responsável) e registra URL + data."""
    destino = ORIG / nome
    registro = json.loads(REGISTRO.read_text()) if REGISTRO.exists() else {}
    if not destino.exists():
        pode, espera = robots(url)
        assert pode, f"robots.txt bloqueia {url}"
        time.sleep(espera)  # Crawl-Delay do site (dadosabertos.poa.br pede 10 s entre requisições)
        r = requests.get(url, timeout=120, headers=HEADERS)
        r.raise_for_status()
        destino.write_bytes(r.content)
        registro[nome] = {"url": url, "data": dt.date.today().isoformat()}
        print(f"baixado: {destino.name} ({len(r.content) / 1024:.0f} KB)")
    elif nome not in registro:  # arquivo baixado antes de existir o registro
        registro[nome] = {"url": url, "data": dt.date.fromtimestamp(destino.stat().st_mtime).isoformat()}
    REGISTRO.write_text(json.dumps(registro, indent=1, ensure_ascii=False) + "\n")
    return destino, registro[nome]["data"]


def ler(arquivo, data_coleta, mancha, url):
    bruto = pd.read_excel(arquivo, sheet_name=0, header=None)
    dados = bruto.iloc[2:, :20]  # pula as 2 linhas de cabeçalho; ignora as colunas de %
    dados.columns = (["cod_ibge", "municipio"]
                     + [f"{c}_afetados" for c in INDICADORES]
                     + [f"{c}_total" for c in INDICADORES])
    dados = dados.dropna(subset=["cod_ibge"])
    dados = dados[pd.to_numeric(dados["cod_ibge"], errors="coerce").notna()]  # descarta notas/rodapé
    num = dados.columns.drop("municipio")
    dados[num] = dados[num].apply(pd.to_numeric).astype("int64")
    dados["municipio"] = dados["municipio"].str.strip()
    dados.insert(2, "mancha", mancha)
    dados["pct_pessoas_afetadas"] = (100 * dados["pessoas_afetados"] / dados["pessoas_total"]).round(2)
    dados["fonte_url"] = url
    dados["data_coleta"] = data_coleta
    return dados


def main():
    ORIG.mkdir(parents=True, exist_ok=True)
    PROC.mkdir(parents=True, exist_ok=True)
    df = pd.concat([ler(*baixar(nome, url), mancha, url)
                    for mancha, (nome, url) in FONTES.items()], ignore_index=True)

    # Checagens: Porto Alegre bate com os PDFs do IBGE e com a população do data.json do INCT
    poa = df[df["municipio"] == "Porto Alegre"].set_index("mancha")
    assert poa.loc["spgg_mup_15mai24", "pessoas_afetados"] == 122663
    assert poa.loc["inpe_ana_v3_19jun24", "pessoas_afetados"] == 152258
    assert (poa["pessoas_total"] == 1332845).all()
    assert not df.duplicated(["cod_ibge", "mancha"]).any()
    assert (df.filter(like="_afetados").values <= df.filter(like="_total").values).all()

    # Malha do RS: todo município da planilha precisa ter polígono no mapa
    malha = json.loads(baixar(*MALHA_RS)[0].read_text())
    codigos = {int(f["properties"]["codarea"]) for f in malha["features"]}
    assert len(codigos) == 497 and set(df["cod_ibge"]) <= codigos, set(df["cod_ibge"]) - codigos

    saida = PROC / "ibge_areas_afetadas.csv"
    df.to_csv(saida, index=False)
    print(f"ok: {saida.relative_to(RAIZ)} -> {len(df)} linhas")
    print(df.groupby("mancha").agg(municipios=("cod_ibge", "nunique"),
                                   pessoas_afetadas=("pessoas_afetados", "sum")))


if __name__ == "__main__":
    main()
