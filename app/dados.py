"""Leitura dos dados processados, formatação em português e peças de gráfico usadas nas duas telas."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

RAIZ = Path(__file__).resolve().parents[1]
PROC = RAIZ / "dados" / "processados"
ORIG = RAIZ / "dados" / "originais"
REPO = "https://github.com/pedroSegabi/trabalhoColeta"

RECORDE = 5.35          # cota máxima do Guaíba no Cais Mauá em maio de 2024
POP_POA = 1_332_845     # Censo 2022 (é a soma da população dos 94 bairros no data.json)
NIVEIS = [round(3 + i / 10, 1) for i in range(71)]  # 3,0 a 10,0 m, de 0,1 em 0,1

# Sistema visual "régua do Guaíba" (paleta segura para daltonismo, sem vermelho de alarme).
# Âmbar só aparece na cota de 5,35 m de maio de 2024; azul são os dados; aqua, a segunda série.
TINTA, TINTA2, LINHA, GRADE = "#15222f", "#4d5b68", "#d6dee4", "#e3e9ee"
AZUL, AQUA, AMBAR, AMBAR_TEXTO = "#2a78d6", "#1baf7a", "#b07800", "#7d5600"
ESCALA = [[0, "#e9eef2"], [0.01, "#cde2fb"], [0.25, "#86b6ef"], [0.5, "#3987e5"], [0.75, "#1c5cab"],
          [1, "#0d366b"]]  # azul sequencial: quase sem cor = 0%, azul escuro = 100%
FONTE, FONTE_NUM = "Public Sans, sans-serif", "Archivo, sans-serif"


# ---------- formatação brasileira ----------
def num(x):
    return f"{x:,.0f}".replace(",", ".")


def pct(x, casas=1):
    return f"{x:.{casas}f}".replace(".", ",") + "%"


def metros(x, casas=1):
    return f"{x:.{casas}f}".replace(".", ",") + "\u00a0m"  # espaço inseparável: "5,3 m" nunca quebra


# ---------- dados ----------
@st.cache_data
def inct(original=False):
    """Simulação do INCT em formato longo (nível x bairro). original=True usa os valores sem nossas correções."""
    df = pd.read_json(PROC / "inct_limpo.json")
    df["nivel_m"] = df["nivel_m"].round(1)
    sufixo = "_orig" if original else ""
    df = df.rename(columns={f"affected_buildings{sufixo}": "predios", f"percentage{sufixo}": "pct",
                            f"affected_population{sufixo}": "pessoas", "total_buildings": "predios_total",
                            "population": "populacao"})
    return df[["nivel_m", "bairro", "predios", "predios_total", "pct", "populacao", "pessoas", "correcao"]]


@st.cache_data
def cidade(original=False):
    """Totais da cidade por nível: pessoas, prédios e bairros atingidos."""
    df = inct(original)
    return df.groupby("nivel_m").agg(pessoas=("pessoas", "sum"), predios=("predios", "sum"),
                                     bairros=("predios", lambda s: (s > 0).sum())).reset_index()


@st.cache_data
def malha_bairros():
    return json.loads((PROC / "bairros_poa.geojson").read_text(encoding="utf-8"))


@st.cache_data
def ibge():
    return pd.read_csv(PROC / "ibge_areas_afetadas.csv")


@st.cache_data
def malha_rs():
    return json.loads((ORIG / "ibge_malha_rs_municipios.geojson").read_text(encoding="utf-8"))


@st.cache_data
def escolas():
    return pd.read_csv(PROC / "escolas_poa.csv")


@st.cache_data
def coleta():
    return json.loads((ORIG / "coleta.json").read_text(encoding="utf-8"))


def nivel_equivalente(pessoas):
    """Nível da simulação em que a cidade chega a esse número de pessoas afetadas (interpolação linear)."""
    c = cidade()  # a curva só sobe com o nível (garantido pela limpeza), então dá para inverter
    return float(np.interp(pessoas, c["pessoas"], c["nivel_m"]))


# ---------- controles ----------
def controle_nivel(chave):
    """O mesmo nível nas duas telas e no endereço da página (?nivel=6,5), para compartilhar um cenário.

    O valor da sessão fica em st.session_state["nivel_sessao"]; cada tela cria o seu controle (chave
    própria) a partir dele. Na primeira visita, o nível vem da URL, se houver um válido.
    """
    if "nivel_sessao" not in st.session_state:
        try:
            da_url = round(float(st.query_params.get("nivel", "").replace(",", ".")), 1)
        except ValueError:
            da_url = None
        st.session_state["nivel_sessao"] = da_url if da_url in NIVEIS else 5.3
    nivel = st.select_slider("Nível do Guaíba em metros (régua do Cais Mauá)", NIVEIS,
                             value=st.session_state["nivel_sessao"], key=chave,
                             format_func=lambda x: f"{x:.1f}".replace(".", ","),
                             help="Arraste ou use as setas do teclado. Em maio de 2024 o Guaíba chegou a 5,35 m.")
    st.session_state["nivel_sessao"] = nivel
    st.query_params["nivel"] = f"{nivel:.1f}".replace(".", ",")
    return nivel


# ---------- peças da página ----------
def regua(nivel):
    """A régua do Cais Mauá (3 a 10 m): água azul até o nível escolhido e a marca âmbar de maio de 2024."""
    def y(m):  # metros -> altura no desenho (3 m embaixo, 10 m em cima)
        return 400 - (m - 3) / 7 * 380
    marcas = "".join(f'<line x1="70" y1="{y(m):.1f}" x2="{86 if m == int(m) else 79}" y2="{y(m):.1f}"/>'
                     for m in (3 + i / 2 for i in range(15)))
    numeros = "".join(f'<text x="60" y="{y(m) + 5:.1f}">{m}{" m" if m == 10 else ""}</text>' for m in range(3, 11))
    agua, cota = y(nivel), y(RECORDE)
    dentro = 400 - agua >= 34  # cabe o número dentro da água? senão, vai logo acima
    rotulo = (f'<text x="95" y="{agua + 25:.1f}" fill="#ffffff"' if dentro
              else f'<text x="95" y="{agua - 8:.1f}" fill="{TINTA}"')
    valor = f"{nivel:.1f}".replace(".", ",")
    return f"""<figure class="regua">
<svg width="230" height="420" viewBox="0 0 230 420" role="img"
 aria-label="Régua do Guaíba: água a {valor} m; marca de maio de 2024 em 5,35 m">
<rect x="70" y="20" width="50" height="380" fill="#ffffff" stroke="#b9c6d0"/>
<rect x="70" y="{agua:.1f}" width="50" height="{400 - agua:.1f}" fill="{AZUL}"/>
<rect x="70" y="{agua:.1f}" width="50" height="3" fill="#1c5cab"/>
<g stroke="{TINTA2}" stroke-width="1.5">{marcas}</g>
<g font-family="{FONTE_NUM}" font-size="15" font-weight="600" fill="{TINTA2}" text-anchor="end">{numeros}</g>
<line x1="64" y1="{cota:.1f}" x2="210" y2="{cota:.1f}" stroke="{AMBAR}" stroke-width="2.5"/>
<text x="128" y="{cota - 10:.1f}" font-family="{FONTE_NUM}" font-size="16" font-weight="700" fill="{AMBAR_TEXTO}">5,35 m</text>
<text x="128" y="{cota + 20:.1f}" font-family="{FONTE}" font-size="13" fill="{AMBAR_TEXTO}">maio de 2024</text>
{rotulo} text-anchor="middle" font-family="{FONTE_NUM}" font-size="17" font-weight="700">{valor}</text>
</svg>
<figcaption>Régua do Cais Mauá. Azul: o nível escolhido. Âmbar: o recorde de maio de 2024.</figcaption>
</figure>"""


def painel(nome):
    """Bloco branco que agrupa um gráfico com o seu título (estilo em app.py, classe .st-key-painel_*)."""
    return st.container(key=f"painel_{nome}")


def nota(html):
    """Aviso discreto com ícone (no lugar do st.info), para as limitações."""
    st.markdown(f'<div class="nota"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#1c5cab" '
            f'stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/>'
            f'<path d="M12 16v-5M12 8h.01"/></svg><p>{html}</p></div>', unsafe_allow_html=True)


# ---------- gráficos ----------
def estilo(fig, altura=380, **layout):
    fig.update_layout(**{"height": altura, "margin": dict(l=8, r=8, t=36, b=8), "separators": ",.",
                         "font": dict(family=FONTE, color=TINTA, size=13), "paper_bgcolor": "rgba(0,0,0,0)",
                         "plot_bgcolor": "rgba(0,0,0,0)", "hoverlabel": dict(font_size=13, font_family=FONTE),
                         **layout})
    fig.update_xaxes(showgrid=False, linecolor="#b9c6d0", tickformat=",.0f", tickfont_color=TINTA2,
                     title_font_color=TINTA2)  # 50.000 em vez de 50k
    fig.update_yaxes(gridcolor=GRADE, zeroline=False, tickformat=",.0f", tickfont_color=TINTA2,
                     title_font_color=TINTA2)
    return fig


def linha_2024(fig, rotulo=True):
    """A cota de maio de 2024 (5,35 m), sempre em âmbar."""
    fig.add_vline(x=RECORDE, line=dict(color=AMBAR, dash="dash", width=2))
    if rotulo:
        fig.add_annotation(x=RECORDE, y=1, yref="paper", text="maio de 2024: 5,35 m", showarrow=False,
                           xanchor="left", yanchor="top", xshift=6, font=dict(color=AMBAR_TEXTO, size=12))
    return fig


def ponto_atual(fig, x, y, texto):
    fig.add_trace(go.Scatter(x=[x], y=[y], mode="markers+text", text=[texto], textposition="middle left",
                             textfont=dict(color=TINTA, size=14, family=FONTE_NUM), hoverinfo="skip",
                             showlegend=False, marker=dict(size=12, color=AZUL, line=dict(width=2, color="white"))))
    return fig


def mapa_bairros(df, altura=540):
    """Mapa coroplético dos 94 bairros (malha oficial da Prefeitura) colorido pelo % de prédios afetados."""
    fig = go.Figure(go.Choroplethmap(
        geojson=malha_bairros(), featureidkey="properties.bairro", locations=df["bairro"], z=df["pct"],
        zmin=0, zmax=100, colorscale=ESCALA, marker=dict(opacity=0.85, line=dict(width=0.6, color="white")),
        customdata=df[["predios", "predios_total", "pessoas"]],
        hovertemplate="<b>%{location}</b><br>%{z:.1f}% dos prédios (%{customdata[0]:,} de %{customdata[1]:,})"
                      "<br>%{customdata[2]:,} pessoas (estimativa)<extra></extra>",
        colorbar=dict(title="% dos prédios", ticksuffix="%", thickness=12, len=0.7)))
    fig.update_layout(map=dict(style="carto-positron", center=dict(lat=-30.12, lon=-51.16), zoom=9.95))
    return estilo(fig, altura, margin=dict(l=0, r=0, t=0, b=0))


INCT_FONTE = ("INCT SiMAI, simulação por bairro (data.json da disciplina, limpo pela equipe)",
              "https://vhlab.com.br/INCT/floods", "10/11/2026")
NOMES_FONTE = {
    "ibge_areas_afetadas_spgg_15mai24.xlsx": "IBGE, áreas afetadas, mancha SPGG-RS/MUP (15/05/2024)",
    "ibge_areas_afetadas_v3_26jun24.xlsx": "IBGE, áreas afetadas, mancha INPE/ANA v3 (19/06/2024)",
    "ibge_malha_rs_municipios.geojson": "IBGE, malha municipal do RS",
    "bairros_lc12112_16.zip": "Prefeitura de POA, bairros oficiais (LC 12.112/2016, os mesmos do ObservaPOA)",
    "cadastro_escolas.csv": "Prefeitura de POA (SMED), cadastro de escolas",
}


def _origem(arquivo):
    """(nome, link, data de coleta) de uma base, lidos do registro de downloads (coleta.json)."""
    if arquivo == "inct":
        return INCT_FONTE
    d = coleta()[arquivo]
    return NOMES_FONTE[arquivo], d["url"], f"{d['data'][8:]}/{d['data'][5:7]}/{d['data'][:4]}"


def fonte(*arquivos):
    """Legenda de fonte embaixo de uma visualização: cada base com link e data de coleta."""
    st.caption("Fonte: " + "; ".join(f"[{n}]({u}), coletado em {d}" for n, u, d in map(_origem, arquivos)) + ".")


def fontes():
    """Tabela de todas as fontes com link e data de coleta (lida do registro de downloads)."""
    linhas = [_origem(a) for a in ["inct", *NOMES_FONTE]]
    st.markdown("| Base | Coleta |\n|---|---|\n" + "\n".join(f"| [{n}]({u}) | {d} |" for n, u, d in linhas))
