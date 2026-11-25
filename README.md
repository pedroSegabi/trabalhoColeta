# Enchentes em Porto Alegre: dashboard alternativo ao INCT SiMAI

Projeto Extensionista: **Coleta, Preparação e Análise de Dados** (PUCRS), Profª Katherine Bianchini Esper de Vargas.

O dashboard responde a duas perguntas:

1. **Tela 1:** se o Guaíba chegar a X metros, quais bairros e quantas pessoas são afetados? (simulação do INCT SiMAI)
2. **Tela 2:** o que a enchente real de 2024 acrescenta? (dados do IBGE sobre as manchas de inundação do MUP/SPGG-RS e do INPE/ANA, e escolas da Prefeitura nos bairros atingidos)

> Os números da simulação são **estimativas**, não previsões nem contagens oficiais.

**Dashboard publicado:** _(link do Streamlit Community Cloud)_

## Equipe

| Nome |
|---|
| Pedro Ernesto |
| Ana Luiza Romanini |
| Enrico Pheula |
| Francisco Cassol |
| Pedro Fam |

## Estrutura

```
app/                 dashboard Streamlit: app.py (entrada), tela1.py, tela2.py, sobre.py, dados.py
dados/originais/     arquivos como vieram (INCT, IBGE, Prefeitura) + coleta.json (URL e data de cada download)
dados/processados/   inct_limpo.json, inct_correcoes.csv, ibge_areas_afetadas.csv, bairros_poa.geojson, escolas_poa.csv
scripts/             coletar_ibge.py, preparar_prefeitura.py, limpar_inct.py, wireframe.py, gerar_pdf.py
notebooks/           eda.ipynb (10 gráficos comentados) + eda.html
relatorios/          base_dados.pdf (Fase 1), limpeza_dados.pdf (Fase 2), dashboard.pdf (Fase 3), wireframes, img/
tests/               test_app.py (as páginas abrem sem erro e os números-chave conferem)
```

## Como rodar

Requer Python 3.11 ou mais recente.

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# dados (os downloads só acontecem na 1ª vez; os arquivos já estão no repositório)
python scripts/coletar_ibge.py          # planilhas do IBGE + malha do RS -> ibge_areas_afetadas.csv
python scripts/limpar_inct.py           # valida e limpa o data.json -> inct_limpo.json + inct_correcoes.csv
python scripts/preparar_prefeitura.py   # bairros e escolas da Prefeitura -> bairros_poa.geojson + escolas_poa.csv

# dashboard
streamlit run app/app.py                # abre em http://localhost:8501
python -m pytest tests/                 # testes do dashboard

# fases anteriores e relatórios
python scripts/wireframe.py
jupyter nbconvert --to notebook --execute --inplace notebooks/eda.ipynb && jupyter nbconvert --to html notebooks/eda.ipynb
for r in base_dados limpeza_dados dashboard; do python scripts/gerar_pdf.py relatorios/$r.md; done   # requer Google Chrome
```

Os scripts terminam com `assert`s de verificação. Se algum dado mudar de forma inesperada, eles param com erro em vez de gerar arquivos errados.

### Publicação (Streamlit Community Cloud)

Em [share.streamlit.io](https://share.streamlit.io): *Create app* → repositório `pedroSegabi/trabalhoColeta`, branch `main`, arquivo `app/app.py`. Em *Advanced settings*, escolha Python 3.12 ou mais recente. O deploy usa `app/requirements.txt`, que só tem o necessário para o dashboard.

## Fontes de dados

| Base | Fonte | Coleta |
|---|---|---|
| Simulação de prédios alagados por bairro (3,0 a 10,0 m) | INCT SiMAI, `data.json` fornecido pela disciplina | arquivo |
| Pessoas, domicílios e estabelecimentos na área afetada, mancha SPGG-RS/MUP de 15/05/2024 | [IBGE, apoio_rs](https://ftp.ibge.gov.br/Informacoes_Gerais_e_Referencia/SINGED_Lab/apoio_rs/Solicitacoes_especiais/08_Secretaria_de_Plan_Gov_e_Gestao_do_RS/) | download automatizado |
| Idem, mancha v3 INPE/ANA de 19/06/2024 | [IBGE, apoio_rs](https://ftp.ibge.gov.br/Informacoes_Gerais_e_Referencia/SINGED_Lab/apoio_rs/Dados_agregados_para_toda_a_area_afetada_v3_Governo_Federal/) | download automatizado |
| Malha municipal do RS | [IBGE, API de malhas v3](https://servicodados.ibge.gov.br/api/docs/malhas?versao=3) | API |
| Limites oficiais dos bairros (LC 12.112/2016), idênticos aos “Bairros Oficiais” do [ObservaPOA](https://prefeitura.poa.br/smpae/observapoa/mapas) | [Prefeitura de POA, dados abertos](https://dadosabertos.poa.br/dataset/a7172700-e0e2-4797-bf4a-12f658828568) (CC-BY) | download automatizado |
| Cadastro de escolas municipais e conveniadas | [Prefeitura de POA, dados abertos (SIE/SMED)](https://dadosabertos.poa.br/dataset/5d204437-8335-43d5-8df3-102a35fc97fb) (CC-BY) | download automatizado |

O painel do MUP (mup.rs.gov.br) é um Power BI sem download nem API. Por isso usamos a agregação oficial que o IBGE fez sobre a mesma mancha (detalhes em `relatorios/base_dados.pdf`).

## Entregas por fase

| Fase | Entrega | Onde |
|---|---|---|
| 1 | Bases de dados (versão final, com as bases usadas) | `relatorios/base_dados.pdf` |
| 2 | Scripts de coleta e limpeza | `scripts/` |
| 2 | JSON do INCT em formato longo e limpo | `dados/processados/inct_limpo.json` |
| 2 | Relatório de limpeza | `relatorios/limpeza_dados.pdf` |
| 2 | Notebook de EDA (10 gráficos) | `notebooks/eda.ipynb` (ou `eda.html`) |
| 2 | Wireframe das duas telas | `relatorios/wireframe_tela1.png`, `wireframe_tela2.png` |
| 3 | Dashboard com as duas telas | `app/` e o link público acima |
| 3 | Relatório do dashboard | `relatorios/dashboard.pdf` |

## Uso de IA

Usamos o Claude Code (Anthropic). Todas as tarefas foram solicitadas pela equipe ao Claude, e todo o resultado foi revisado pela equipe. O registro detalhado está na seção 7 de `relatorios/limpeza_dados.pdf` (Fase 2) e na seção 10 de `relatorios/dashboard.pdf` (Fase 3).
