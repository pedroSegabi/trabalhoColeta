"""Tela 1: se o Guaíba chegar a X metros, quais bairros e quantas pessoas são afetados?"""
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dados import (AZUL, GRADE, POP_POA, cidade, controle_nivel, estilo, fonte, inct, linha_2024, mapa_bairros,
                   metros, nota, num, painel, pct, ponto_atual, regua)

# ---------- barra do nível: fica fixa no topo enquanto a página rola (CSS em app.py) ----------
with st.container(key="barra_nivel"):
    c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
    with c1:
        nivel = controle_nivel("nivel_t1")
    with c2:
        original = st.toggle("Ver dados originais do INCT", key="original",
                             help="Sem as nossas correções: percentuais arredondados para cima e 17 valores "
                                  "inconsistentes.")

df = inct(original)
agora = df[df["nivel_m"] == nivel]
atingidos = agora[agora["predios"] > 0].sort_values("pct")
tot, outro = cidade(original), cidade(not original)
linha, comp = tot[tot["nivel_m"] == nivel].iloc[0], outro[outro["nivel_m"] == nivel].iloc[0]

# ---------- a resposta: frase, números e a régua ----------
topo, lado = st.columns([3, 1], gap="large")
with topo:
    st.title(f"Com o Guaíba a {metros(nivel)}, a água alcançaria {num(linha['bairros'])} dos 94 bairros "
             f"e cerca de {num(round(linha['pessoas'] / 1000))} mil pessoas.", anchor=False)
    k1, k2, k3 = st.columns(3)
    k1.metric("Pessoas afetadas (estimativa)", num(linha["pessoas"]))
    k1.caption(f"{pct(100 * linha['pessoas'] / POP_POA)} da cidade. "
               f"{'Corrigido' if original else 'Original do INCT'}: {num(comp['pessoas'])}")
    k2.metric("Prédios afetados", num(linha["predios"]))
    k2.caption(f"{pct(100 * linha['predios'] / agora['predios_total'].sum())} dos "
               f"{num(agora['predios_total'].sum())} prédios")
    k3.metric("Bairros atingidos", f"{num(linha['bairros'])} de 94")
    k3.caption(f"{(agora['pct'] >= 50).sum()} com metade ou mais dos prédios")
    if original:
        st.caption(":material/warning: Você está vendo os **valores originais** do INCT, sem as correções.")
    nota("Estimativas de uma simulação do INCT SiMAI, não previsão nem contagem oficial. A população de cada "
         "bairro é dividida igualmente entre todos os seus prédios, inclusive os não residenciais (OpenStreetMap). "
         'Corrigimos 17 valores do arquivo original; veja <a href="sobre" target="_self">Sobre os dados</a>.')
with lado:
    st.markdown(regua(nivel), unsafe_allow_html=True)  # st.html removeria o SVG

# ---------- onde a água chega ----------
st.header(f"Onde a água chega a {metros(nivel)}", anchor=False,
          help="Percentual de prédios afetados em cada bairro, na malha oficial da Prefeitura (LC 12.112/2016). "
               "Passe o mouse sobre um bairro ou uma barra para ver os números.")
m, b = st.columns([3, 2], gap="medium")
with m, painel("mapa"):
    aba_mapa, aba_anim = st.tabs(["Mapa no nível escolhido", "Animação de 3 a 10 m"])
    with aba_mapa:
        st.plotly_chart(mapa_bairros(agora), config={"scrollZoom": True})
    with aba_anim:
        niveis = sorted(df["nivel_m"].unique())
        base = mapa_bairros(agora, altura=560)  # começa no nível escolhido no controle
        base.update_traces(hovertemplate="<b>%{location}</b><br>%{z:.1f}% dos prédios<extra></extra>")
        # cada quadro troca só as cores (z); a malha é enviada uma vez só
        base.frames = [go.Frame(name=metros(n), data=[go.Choroplethmap(z=df.loc[df["nivel_m"] == n, "pct"])])
                       for n in niveis]
        passo = dict(frame=dict(duration=250, redraw=True), transition=dict(duration=0), mode="immediate")
        base.update_layout(  # botão e régua abaixo do mapa, para não cobrir os bairros
            margin=dict(l=0, r=0, t=0, b=95),
            updatemenus=[dict(type="buttons", x=0, y=0, xanchor="left", yanchor="top", showactive=False,
                              direction="left", pad=dict(t=12),
                              buttons=[dict(label="▶ Reproduzir", method="animate", args=[None, passo]),
                                       dict(label="❚❚ Pausar", method="animate", args=[[None], passo])])],
            sliders=[dict(active=niveis.index(nivel), x=0.3, len=0.7, y=0, yanchor="top", pad=dict(t=8),
                          currentvalue=dict(prefix="Nível: ", xanchor="right", font=dict(size=14)),
                          steps=[dict(label=metros(n), method="animate", args=[[metros(n)], passo])
                                 for n in niveis])])
        st.plotly_chart(base, key="animacao")
with b, painel("barras"):
    st.subheader(f"{len(atingidos)} bairros atingidos, em ordem", anchor=False)
    if atingidos.empty:
        st.write("Nenhum bairro atingido neste nível.")
    else:
        fig = px.bar(atingidos, x="pct", y="bairro", orientation="h", range_x=[0, 100],
                     custom_data=["predios", "predios_total", "pessoas"])
        fig.update_traces(marker_color=AZUL, hovertemplate="<b>%{y}</b><br>%{x:.1f}% dos prédios "
                          "(%{customdata[0]:,} de %{customdata[1]:,})<br>%{customdata[2]:,} pessoas<extra></extra>")
        estilo(fig, max(300, 19 * len(atingidos) + 60), xaxis_title=None, yaxis_title=None, bargap=0.25)
        fig.update_xaxes(ticksuffix="%", side="top", showgrid=True, gridcolor=GRADE)
        with st.container(height=520, border=False):
            st.plotly_chart(fig, config={"displayModeBar": False})

# ---------- a cidade inteira ----------
st.header("Na cidade inteira", anchor=False)
g, r = st.columns(2, gap="medium")
with g, painel("curva"):
    st.subheader("Pessoas afetadas conforme o rio sobe", anchor=False,
                 help="Estimativa para a cidade inteira, de 3,0 a 10,0 m. A linha âmbar é o recorde de maio de "
                      "2024 (5,35 m); o ponto azul é o nível escolhido.")
    fig = px.line(tot, x="nivel_m", y="pessoas")
    fig.update_traces(line=dict(color=AZUL, width=2.5),
                      hovertemplate="%{x:.1f} m: %{y:,} pessoas<extra></extra>")
    linha_2024(fig)
    ponto_atual(fig, nivel, linha["pessoas"], f"{num(linha['pessoas'])}  ")
    estilo(fig, 380, xaxis_title="nível do Guaíba (m)", yaxis_title="pessoas afetadas (estimativa)",
           hovermode="x unified", margin=dict(l=8, r=8, t=24, b=8))
    fig.update_xaxes(ticksuffix=" m")
    st.plotly_chart(fig)
with r, painel("ranking"):
    st.subheader(f"Bairros com mais pessoas afetadas a {metros(nivel)}", anchor=False,
                 help="Os 10 maiores pelo número estimado de pessoas. Bairros grandes e pouco alagados podem "
                      "somar mais pessoas do que bairros pequenos e 100% alagados.")
    ranking = agora[agora["pessoas"] > 0].nlargest(10, "pessoas")[["bairro", "pessoas", "pct", "predios"]]
    ranking["pct"] /= 100  # a coluna de progresso formata frações como % no padrão do navegador
    st.dataframe(ranking, hide_index=True, height=390, column_config={
        "bairro": "Bairro",
        "pessoas": st.column_config.NumberColumn("Pessoas (estim.)", format="localized"),
        "pct": st.column_config.ProgressColumn("% dos prédios", format="percent", min_value=0, max_value=1),
        "predios": st.column_config.NumberColumn("Prédios afetados", format="localized"),
    })

# ---------- ferramenta: seu bairro ----------
st.header("Consulte um bairro", anchor=False, help="A partir de que nível o bairro começa a ser atingido.")
with painel("bairro"):
    s1, s2 = st.columns([1, 2], gap="large")
    with s1:
        nomes = sorted(df["bairro"].unique())
        bairro = st.selectbox("Bairro", nomes, index=nomes.index("Menino Deus"))
        serie = df[df["bairro"] == bairro]
        molhado = serie[serie["predios"] > 0]
        metade = serie[serie["pct"] >= 50]
        hoje = serie[serie["nivel_m"] == nivel].iloc[0]
        if molhado.empty:
            st.success("Na simulação, nenhum prédio deste bairro é afetado nem com o rio a 10 m.",
                       icon=":material/check_circle:")
        else:
            st.metric("Começa a ter prédios afetados em", metros(molhado["nivel_m"].min()))
            st.metric("Metade dos prédios afetados em",
                      metros(metade["nivel_m"].min()) if len(metade) else "não chega")
        st.metric(f"A {metros(nivel)}", f"{pct(hoje['pct'])} dos prédios",
                  help=f"{num(hoje['predios'])} de {num(hoje['predios_total'])} prédios; "
                       f"{num(hoje['pessoas'])} de {num(hoje['populacao'])} moradores (estimativa).")
    with s2:
        fig = px.area(serie, x="nivel_m", y="pct")
        fig.update_traces(line=dict(color=AZUL, width=2), fillcolor="rgba(42,120,214,0.14)",
                          hovertemplate="%{x:.1f} m: %{y:.1f}% dos prédios<extra></extra>")
        linha_2024(fig)
        ponto_atual(fig, nivel, hoje["pct"], f"{pct(hoje['pct'])}  ")
        estilo(fig, 340, xaxis_title="nível do Guaíba (m)", yaxis_title=f"% dos prédios de {bairro}",
               hovermode="x unified")
        fig.update_xaxes(ticksuffix=" m")
        fig.update_yaxes(range=[0, 105], ticksuffix="%")
        st.plotly_chart(fig)

# ---------- downloads e fonte ----------
colunas = {"nivel_m": "nivel_m", "bairro": "bairro", "predios": "predios_afetados", "predios_total": "predios_total",
           "pct": "pct_predios_afetados", "populacao": "populacao", "pessoas": "pessoas_afetadas_estimativa"}
versao = "original" if original else "corrigido"
st.divider()
d1, d2, d3 = st.columns([1, 1, 2], vertical_alignment="center")
d1.download_button(f"Baixar bairros a {metros(nivel)} (CSV)",
                   agora[list(colunas)].rename(columns=colunas).to_csv(index=False),
                   f"inct_{versao}_{nivel:.1f}m.csv", "text/csv", icon=":material/download:")
d2.download_button("Baixar todos os níveis (CSV)", df[list(colunas)].rename(columns=colunas).to_csv(index=False),
                   f"inct_{versao}_todos_niveis.csv", "text/csv", icon=":material/download:")
with d3:
    st.caption(f"Os arquivos seguem a opção escolhida no topo ({'dados originais do INCT' if original else 'dados corrigidos'}).")
fonte("inct", "bairros_lc12112_16.zip")
