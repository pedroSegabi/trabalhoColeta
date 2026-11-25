"""Tela 2: o que a enchente real de 2024 acrescenta à simulação?"""
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dados import (AQUA, AZUL, ESCALA, GRADE, TINTA2, cidade, controle_nivel, escolas, estilo, fonte, fontes, ibge, inct,
                   linha_2024, malha_rs, metros, nivel_equivalente, num, painel, ponto_atual)

MANCHAS = {"inpe_ana_v3_19jun24": "INPE/ANA, final (19/06)",
           "spgg_mup_15mai24": "SPGG-RS/MUP, pico (15/05)"}
ARQUIVO = {"inpe_ana_v3_19jun24": "ibge_areas_afetadas_v3_26jun24.xlsx",
           "spgg_mup_15mai24": "ibge_areas_afetadas_spgg_15mai24.xlsx"}
INDICADORES = {"Pessoas": "pessoas", "Domicílios": "domicilios_particulares",
               "Escolas (estab. de ensino)": "estab_ensino", "Unidades de saúde": "estab_saude",
               "Estab. agropecuários": "estab_agropecuarios"}

# ---------- cabeçalho: a resposta em uma frase ----------
titulo = st.empty()  # a frase depende da mancha escolhida dentro da aba do RS
st.markdown("Dados reais da enchente de 2024, do IBGE, e as escolas nos bairros que a simulação aponta como "
            "atingidos. Escolha uma aba.")
aba_rs, aba_poa = st.tabs(["Rio Grande do Sul", "Porto Alegre"])

# =============== aba 1: municípios do RS ===============
with aba_rs:
    f1, f2, f3 = st.columns([5, 4, 2], vertical_alignment="bottom")
    with f1:
        mancha = st.segmented_control("Mancha de inundação", list(MANCHAS), format_func=MANCHAS.get, required=True,
                                      default="inpe_ana_v3_19jun24",
                                      help="Duas delimitações oficiais da área alagada; o IBGE cruzou cada uma "
                                           "com o Censo 2022.")
    rotulo = f2.selectbox("Indicador", list(INDICADORES))
    top = f3.slider("Municípios no ranking", 5, 30, 15)
    ind = INDICADORES[rotulo]

    todos = ibge()[lambda d: d["mancha"] == mancha]
    rs = todos.copy()
    rs["valor"] = rs[f"{ind}_afetados"]
    rs["pct"] = (100 * rs["valor"] / rs[f"{ind}_total"].where(rs[f"{ind}_total"] > 0)).fillna(0)
    rs = rs[rs["valor"] > 0]

    k = st.columns(4)
    k[0].metric("Municípios atingidos", num((todos["pessoas_afetados"] > 0).sum()),
                help="Municípios com moradores dentro da área inundada.")
    for col, (nome, c) in zip(k[1:], [("Pessoas na área inundada", "pessoas"), ("Escolas na área", "estab_ensino"),
                                      ("Unidades de saúde na área", "estab_saude")]):
        col.metric(nome, num(todos[f"{c}_afetados"].sum()))

    m, b = st.columns([3, 2], gap="medium")
    with m, painel("mapa_rs"):
        st.subheader(f"{rotulo}: % do município na área inundada", anchor=False,
                     help="O mapa usa o percentual: em números absolutos, só as cidades grandes apareceriam. "
                          "Cinza claro: sem área inundada nesta mancha.")
        geo = malha_rs()
        fig = go.Figure(go.Choroplethmap(  # fundo: todos os 497 municípios, sem cor
            geojson=geo, featureidkey="properties.codarea",
            locations=[f["properties"]["codarea"] for f in geo["features"]], z=[0] * len(geo["features"]),
            colorscale=[[0, "#e9eef2"], [1, "#e9eef2"]], showscale=False, hoverinfo="skip",
            marker=dict(line=dict(width=0.3, color="white"))))
        fig.add_trace(go.Choroplethmap(
            geojson=geo, featureidkey="properties.codarea", locations=rs["cod_ibge"].astype(str), z=rs["pct"],
            zmin=0, zmax=max(rs["pct"].max(), 1), colorscale=ESCALA, marker=dict(line=dict(width=0.3, color="white")),
            customdata=rs[["municipio", "valor"]],
            hovertemplate="<b>%{customdata[0]}</b><br>%{z:.1f}% do município<br>%{customdata[1]:,} na área"
                          "<extra></extra>", colorbar=dict(ticksuffix="%", thickness=12, len=0.7)))
        fig.update_layout(map=dict(style="carto-positron", center=dict(lat=-30.1, lon=-53.3), zoom=5.4))
        st.plotly_chart(estilo(fig, 500, margin=dict(l=0, r=0, t=0, b=0)), config={"scrollZoom": True})
    with b, painel("ranking_rs"):
        st.subheader(f"{top} municípios com mais {rotulo.lower()} na área", anchor=False)
        medida = st.segmented_control("Ordenar por", ["Quantidade", "% do município"], default="Quantidade",
                                      required=True)
        col = "pct" if medida == "% do município" else "valor"
        maiores = rs.nlargest(top, col).sort_values(col)
        fig = px.bar(maiores, x=col, y="municipio", orientation="h", custom_data=["valor", "pct"])
        fig.update_traces(marker_color=AZUL, hovertemplate="<b>%{y}</b><br>%{customdata[0]:,} na área inundada"
                                                           "<br>%{customdata[1]:.1f}% do município<extra></extra>")
        estilo(fig, 430, xaxis_title=None, yaxis_title=None, bargap=0.25, margin=dict(l=8, r=8, t=8, b=8))
        fig.update_xaxes(showgrid=True, gridcolor=GRADE, ticksuffix="%" if col == "pct" else "")
        st.plotly_chart(fig, config={"displayModeBar": False})

    with painel("estab_rs"):
        st.subheader("Escolas e unidades de saúde na área inundada", anchor=False,
                     help="Municípios com mais estabelecimentos de ensino e de saúde dentro da mancha escolhida.")
        es = todos.assign(total=lambda d: d["estab_ensino_afetados"] + d["estab_saude_afetados"]).nlargest(top, "total")
        fig = go.Figure([go.Bar(x=es["municipio"], y=es[f"estab_{c}_afetados"], name=n, marker_color=cor,
                                hovertemplate="<b>%{x}</b><br>%{y} " + n.lower() + "<extra></extra>")
                         for c, n, cor in [("ensino", "Escolas", AZUL), ("saude", "Unidades de saúde", AQUA)]])
        estilo(fig, 340, barmode="group", bargap=0.3, bargroupgap=0.08, yaxis_title="estabelecimentos",
               legend=dict(orientation="h", y=1.1, x=0))
        st.plotly_chart(fig)
    fonte(ARQUIVO[mancha], "ibge_malha_rs_municipios.geojson")

titulo.title(f"Em 2024, {num(todos['pessoas_afetados'].sum())} pessoas no Rio Grande do Sul moravam dentro "
             "da área inundada.", anchor=False)

# =============== aba 2: Porto Alegre (simulação x 2024 e escolas) ===============
with aba_poa:
    nivel = controle_nivel("nivel_t2")
    poa = ibge()[ibge()["municipio"] == "Porto Alegre"].set_index("mancha")["pessoas_afetados"]
    tot = cidade()
    atual = tot.loc[tot["nivel_m"] == nivel, "pessoas"].iloc[0]

    st.header("A simulação bate com 2024?", anchor=False,
              help="A curva é a simulação da Tela 1. As linhas pontilhadas são os moradores contados pelo IBGE "
                   "dentro das duas manchas oficiais de 2024.")
    with painel("comparacao"):
        g, t = st.columns([3, 2], gap="large")
        with g:
            fig = px.line(tot, x="nivel_m", y="pessoas")
            fig.update_traces(line=dict(color=AZUL, width=2.5), name="Simulação INCT", showlegend=True,
                              hovertemplate="%{x:.1f} m: %{y:,} pessoas<extra></extra>")
            for chave, nome in [("spgg_mup_15mai24", "SPGG-RS/MUP"), ("inpe_ana_v3_19jun24", "INPE/ANA v3")]:
                fig.add_hline(y=poa[chave], line=dict(color=TINTA2, dash="dot", width=1.5))
                fig.add_annotation(x=10.0, y=poa[chave], text=f"IBGE, mancha {nome}: {num(poa[chave])}",
                                   showarrow=False, xanchor="right", yanchor="bottom",
                                   font=dict(color=TINTA2, size=12))
            linha_2024(fig)
            ponto_atual(fig, nivel, atual, f"{num(atual)}  ")
            estilo(fig, 400, xaxis_title="nível do Guaíba (m)", yaxis_title="pessoas", showlegend=False)
            fig.update_xaxes(ticksuffix=" m")
            st.plotly_chart(fig)
        with t:
            n1, n2 = nivel_equivalente(poa["spgg_mup_15mai24"]), nivel_equivalente(poa["inpe_ana_v3_19jun24"])
            st.metric(f"Simulação a {metros(nivel)}", f"{num(atual)} pessoas")
            st.markdown(
                f"Os moradores contados pelo IBGE aparecem na simulação entre **{metros(n1)}** e **{metros(n2)}**. "
                f"O rio chegou a **5,35\u00a0m**, dentro dessa faixa: a simulação é coerente com o que aconteceu.\n\n"
                "Mesmo as duas manchas oficiais diferem em cerca de 30 mil pessoas, então os números valem como "
                "**ordem de grandeza**.")
    fonte("inct", "ibge_areas_afetadas_spgg_15mai24.xlsx", "ibge_areas_afetadas_v3_26jun24.xlsx")

    st.header("Escolas nos bairros atingidos", anchor=False,
              help="Escolas municipais e conveniadas (cadastro da SMED). A simulação é por bairro: uma escola num "
                   "bairro atingido não quer dizer que o prédio da escola alagou.")
    redes = st.pills("Rede", ["Municipal", "Conveniada"], default=["Municipal", "Conveniada"], selection_mode="multi")
    esc = escolas()[lambda d: d["rede"].isin(redes)]
    df = inct()
    agora = df[df["nivel_m"] == nivel].set_index("bairro")
    esc = esc.assign(pct_bairro=esc["bairro"].map(agora["pct"]))
    afetadas = esc[esc["pct_bairro"] > 0]

    e1, e2, e3 = st.columns(3)
    e1.metric(f"Escolas em bairros atingidos a {metros(nivel)}", f"{len(afetadas)} de {len(esc)}")
    e2.metric("Em bairros com ≥ 50% dos prédios afetados", num((esc["pct_bairro"] >= 50).sum()))
    e3.metric("Bairros atingidos com escola", num(afetadas["bairro"].nunique()))

    c1, c2 = st.columns(2, gap="medium")
    with c1, painel("escolas_curva"):
        st.subheader("Escolas conforme o rio sobe", anchor=False)
        por_nivel = df.merge(esc.groupby("bairro").size().rename("escolas"), left_on="bairro", right_index=True)
        curva = por_nivel.assign(atingido=por_nivel["escolas"].where(por_nivel["predios"] > 0, 0),
                                 metade=por_nivel["escolas"].where(por_nivel["pct"] >= 50, 0)) \
            .groupby("nivel_m")[["atingido", "metade"]].sum().reset_index()
        fig = go.Figure([go.Scatter(x=curva["nivel_m"], y=curva[c], name=n, line=dict(color=cor, width=2.5),
                                    hovertemplate="%{y} escolas<extra>" + n + "</extra>")
                         for c, n, cor in [("atingido", "em bairros atingidos", AZUL),
                                           ("metade", "em bairros com ≥ 50% dos prédios afetados", AQUA)]])
        linha_2024(fig)
        fig.add_vline(x=nivel, line=dict(color=AZUL, width=1))
        estilo(fig, 380, xaxis_title="nível do Guaíba (m)", yaxis_title="escolas", hovermode="x unified",
               legend=dict(orientation="h", y=1.02, x=0, yanchor="bottom"), margin=dict(l=8, r=8, t=56, b=8))
        fig.update_xaxes(ticksuffix=" m")
        st.plotly_chart(fig)
    with c2, painel("escolas_bairros"):
        st.subheader(f"Escolas por bairro atingido a {metros(nivel)}", anchor=False)
        if afetadas.empty:
            st.write("Nenhuma escola em bairro atingido neste nível.")
        else:
            cont = afetadas.groupby(["bairro", "rede"]).size().rename("escolas").reset_index()
            ordem = afetadas["bairro"].value_counts().sort_values().index.tolist()
            fig = px.bar(cont, x="escolas", y="bairro", color="rede", orientation="h",
                         category_orders={"bairro": ordem[::-1], "rede": ["Municipal", "Conveniada"]},
                         color_discrete_map={"Municipal": AZUL, "Conveniada": AQUA})
            fig.update_traces(marker_line=dict(width=1, color="white"),
                              hovertemplate="<b>%{y}</b><br>%{x} escolas<extra>%{fullData.name}</extra>")
            estilo(fig, max(320, 22 * len(ordem) + 90), xaxis_title=None, yaxis_title=None, bargap=0.25,
                   legend=dict(orientation="h", y=1.0, x=0, yanchor="bottom", title=None),
                   margin=dict(l=8, r=8, t=30, b=8))
            with st.container(height=380, border=False):
                st.plotly_chart(fig, config={"displayModeBar": False})

    with st.expander(f"Lista das {len(afetadas)} escolas em bairros atingidos a {metros(nivel)}"):
        st.dataframe(afetadas.sort_values("pct_bairro", ascending=False)[["escola", "rede", "bairro", "pct_bairro"]]
                     .assign(pct_bairro=lambda d: d["pct_bairro"] / 100),
                     hide_index=True, column_config={
                         "escola": "Escola", "rede": "Rede", "bairro": "Bairro",
                         "pct_bairro": st.column_config.ProgressColumn("% dos prédios do bairro afetados",
                                                                       format="percent", min_value=0, max_value=1)})
    fonte("inct", "cadastro_escolas.csv", "bairros_lc12112_16.zip")

# ---------- fontes de tudo ----------
st.divider()
st.subheader("Fontes", anchor=False)
fontes()
