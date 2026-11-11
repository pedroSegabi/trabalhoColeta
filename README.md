# Enchentes em Porto Alegre: dashboard alternativo ao INCT SiMAI

Projeto Extensionista: **Coleta, Preparação e Análise de Dados** (PUCRS), Profª Katherine Bianchini Esper de Vargas.

O dashboard responde a duas perguntas:

1. **Tela 1:** se o Guaíba chegar a X metros, quais bairros e quantas pessoas são afetados? (simulação do INCT SiMAI)
2. **Tela 2:** o que a enchente real de 2024 acrescenta? (dados do IBGE sobre as manchas de inundação do MUP/SPGG-RS e do INPE/ANA)

> Os números da simulação são **estimativas**, não previsões nem contagens oficiais.

## Equipe

| Nome |
|---|
| Pedro Ernesto |
| Ana Luiza Romanini |
| Enrico Pheula |
| Fransico Cassol |
| Pedro Fam |

**Dashboard publicado:** _(Fase 3)_

## Estrutura

```
dados/originais/     data.json do INCT + planilhas do IBGE (como vieram)
dados/processados/   inct_limpo.json, inct_correcoes.csv, ibge_areas_afetadas.csv
scripts/             coletar_ibge.py, limpar_inct.py, wireframe.py, gerar_pdf.py
notebooks/           eda.ipynb (10 gráficos comentados) + eda.html
relatorios/          limpeza_dados.pdf, wireframe_tela1.png, wireframe_tela2.png
app/                 dashboard (Fase 3)
```

## Como rodar

Requer Python 3.11 ou mais recente.

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python scripts/coletar_ibge.py     # baixa as planilhas do IBGE (só na 1ª vez) e gera o CSV limpo
python scripts/limpar_inct.py      # valida e limpa o data.json -> inct_limpo.json + inct_correcoes.csv
python scripts/wireframe.py        # gera os esboços das telas
jupyter nbconvert --to notebook --execute --inplace notebooks/eda.ipynb
jupyter nbconvert --to html notebooks/eda.ipynb
python scripts/gerar_pdf.py relatorios/limpeza_dados.md   # requer Google Chrome
```

Os scripts terminam com `assert`s de verificação. Se algum dado mudar de forma inesperada, eles param com erro em vez de gerar arquivos errados.

## Fontes de dados

| Base | Fonte | Coleta |
|---|---|---|
| Simulação de prédios alagados por bairro (3,0 a 10,0 m) | INCT SiMAI, `data.json` fornecido pela disciplina | arquivo |
| Pessoas, domicílios e estabelecimentos na área afetada, mancha SPGG-RS/MUP de 15/05/2024 | [IBGE, apoio_rs](https://ftp.ibge.gov.br/Informacoes_Gerais_e_Referencia/SINGED_Lab/apoio_rs/Solicitacoes_especiais/08_Secretaria_de_Plan_Gov_e_Gestao_do_RS/) | download automatizado |
| Idem, mancha v3 INPE/ANA de 19/06/2024 | [IBGE, apoio_rs](https://ftp.ibge.gov.br/Informacoes_Gerais_e_Referencia/SINGED_Lab/apoio_rs/Dados_agregados_para_toda_a_area_afetada_v3_Governo_Federal/) | download automatizado |

O painel do MUP (mup.rs.gov.br) é um Power BI sem download nem API. Por isso usamos a agregação oficial que o IBGE fez sobre a mesma mancha (detalhes em `relatorios/limpeza_dados.pdf`, seção 4).

## Entregas por fase

| Fase | Entrega | Onde |
|---|---|---|
| 2 | Scripts de coleta | `scripts/coletar_ibge.py` |
| 2 | JSON do INCT em formato longo e limpo | `dados/processados/inct_limpo.json` |
| 2 | Relatório de limpeza | `relatorios/limpeza_dados.pdf` |
| 2 | Notebook de EDA (10 gráficos) | `notebooks/eda.ipynb` (ou `eda.html`) |
| 2 | Wireframe das duas telas | `relatorios/wireframe_tela1.png`, `wireframe_tela2.png` |

## Uso de IA

Usamos o Claude Code (Anthropic) nesta fase. Todas as tarefas foram solicitadas pela equipe ao Claude, e todo o resultado foi revisado pela equipe. O registro detalhado está na seção 7 de `relatorios/limpeza_dados.pdf`.
