"""Dashboard: enchentes em Porto Alegre. Rodar com:  streamlit run app/app.py"""
import streamlit as st

st.set_page_config(page_title="Enchentes em Porto Alegre", page_icon=":material/water:", layout="wide")

# Sistema visual "régua do Guaíba": Archivo (títulos e números) + Public Sans (texto, pelo tema).
# Cores e fonte do texto estão em .streamlit/config.toml; aqui só o que o tema não cobre.
st.html("""<style>
@import url('https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@75..100,500..800&display=swap');
h1, h2, h3, [data-testid="stMetricValue"] {
  font-family: 'Archivo', sans-serif !important; font-stretch: 85%; font-variant-numeric: tabular-nums;
}
h1 { font-size: 2.75rem !important; line-height: 1.08 !important; font-weight: 700 !important;
     letter-spacing: -0.01em; max-width: 26ch; padding-bottom: 0.25rem !important; }
h2 { font-size: 1.75rem !important; font-weight: 700 !important; padding-top: 2.25rem !important; }
[data-testid="stMainBlockContainer"] { max-width: 1280px; padding-top: 4.5rem; }
[data-testid="stMetricValue"] { font-size: 2.5rem !important; font-weight: 700; line-height: 1.05; }
[data-testid="stCaptionContainer"] { color: #4d5b68; }
.nota { display: flex; gap: 12px; align-items: flex-start; background: #e6eef5; border-radius: 6px;
        padding: 14px 16px; max-width: 72ch; font-size: 0.95rem; line-height: 1.5; }
.nota svg { flex: none; margin-top: 2px; } .nota p { margin: 0; } .nota a { color: #1c5cab; }
.regua { margin: 0; } .regua figcaption { font-size: 0.85rem; color: #4d5b68; max-width: 230px; }
:focus-visible { outline: 3px solid #2a78d6 !important; outline-offset: 2px; }
h3 { font-size: 1.2rem !important; font-weight: 700 !important; padding-top: 0.25rem !important; }
/* painéis: cada gráfico fica num bloco branco com o seu título (dados.painel) */
[class*="st-key-painel_"] { background: #ffffff; border: 1px solid #d6dee4; border-radius: 10px;
                            padding: 16px 20px 6px; }
/* barra do nível da Tela 1: fica fixa no topo ao rolar a página */
/* (o sticky vai no invólucro do Streamlit, que é filho direto da coluna principal da página) */
[data-testid="stLayoutWrapper"]:has(> .st-key-barra_nivel) { position: sticky; top: 3.75rem; z-index: 990; }
.st-key-barra_nivel { background: #f4f7f9;
                      border-bottom: 1px solid #d6dee4; padding: 4px 0 10px; }
/* abas da Tela 2 mais visíveis */
[data-testid="stTab"] p { font-size: 1.1rem !important; font-weight: 600; } [data-testid="stTab"] { padding: 6px 4px; }
@media (max-width: 640px) {
  h1 { font-size: 1.85rem !important; } h2 { font-size: 1.4rem !important; }
  [data-testid="stMetricValue"] { font-size: 2rem !important; }
}
</style>""")

st.navigation([
    st.Page("tela1.py", title="Tela 1: simulação", default=True),
    st.Page("tela2.py", title="Tela 2: enchente de 2024"),
    st.Page("sobre.py", title="Sobre os dados"),
], position="top").run()
