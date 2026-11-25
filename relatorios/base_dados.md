# Relatório de Bases de Dados: Fase 1 (versão final)

Projeto Extensionista: Análise de Dados de Enchentes do INCT SiMAI

Coleta, Preparação e Análise de Dados (PUCRS), Profª Katherine Bianchini Esper de Vargas

Equipe: Pedro Ernesto, Ana Luiza Romanini, Enrico Pheula, Fransico Cassol, Pedro Fam

Data: 24/11/2026 (atualizado com as bases efetivamente usadas no dashboard)

---

## 1. Perguntas do dashboard

- **Tela 1:** se o Guaíba chegar a X metros, quais bairros de Porto Alegre e quantas pessoas são afetados? Responde com a simulação do INCT.
- **Tela 2:** o que a enchente real de 2024 acrescenta à simulação? Quantas pessoas, domicílios, escolas e unidades de saúde ficaram dentro das áreas inundadas no RS? Os números da simulação para Porto Alegre são coerentes com o que aconteceu? Quais escolas ficam nos bairros que a simulação aponta como atingidos?

## 2. Resumo das bases

| # | Base | Fonte | Formato | Coleta | Data | Licença | Uso |
|---|---|---|---|---|---|---|---|
| 1 | Simulação de prédios alagados por bairro | INCT SiMAI | JSON | Arquivo da disciplina (Moodle) | 10/11/2026 | Uso acadêmico na disciplina | Tela 1 e Tela 2 |
| 2 | Pessoas, domicílios e estabelecimentos nas áreas afetadas, mancha SPGG-RS/MUP | IBGE | XLSX | Download automatizado | 10/11/2026 | Dados públicos do IBGE, uso livre com citação | Tela 2 |
| 3 | Idem, mancha INPE/ANA v3 | IBGE | XLSX | Download automatizado | 10/11/2026 | Idem | Tela 2 |
| 4 | Malha municipal do RS | IBGE, API de malhas v3 | GeoJSON | API (download automatizado) | 24/11/2026 | Idem | Mapa da Tela 2 |
| 5 | Limites oficiais dos bairros (LC 12.112/2016) | Prefeitura de POA, dadosabertos.poa.br (idêntico ao do ObservaPOA) | Shapefile (ZIP) | Download automatizado | 24/11/2026 | CC-BY | Mapa da Tela 1 |
| 6 | Cadastro de escolas municipais e conveniadas (SIE/SMED) | Prefeitura de POA, dadosabertos.poa.br | CSV (`;`) | Download automatizado | 24/11/2026 | CC-BY | Escolas na Tela 2 |

As URLs exatas e as datas de coleta ficam registradas em `dados/originais/coleta.json`, gerado pelos scripts. O dashboard mostra a mesma tabela na seção *Fontes*.

### Recorte e ligação com o INCT

| Base | Recorte espacial | Recorte temporal | Como se liga aos dados do INCT |
|---|---|---|---|
| 1. Simulação do INCT | 94 bairros de Porto Alegre | Níveis de 3,0 a 10,0 m; população do Censo 2022; prédios do OpenStreetMap | É a base da Tela 1 |
| 2. IBGE, mancha SPGG-RS/MUP | 223 municípios do RS dentro da mancha | Mancha de 15/05/2024; moradores do Censo 2022 | Porto Alegre (122.663 moradores na mancha) é comparada à curva da simulação; a população total de POA é igual à do `data.json` |
| 3. IBGE, mancha INPE/ANA v3 | 345 municípios do RS dentro da mancha | Mancha de 19/06/2024; moradores do Censo 2022 | Idem, com 152.258 moradores de POA na mancha |
| 4. Malha municipal do RS | 497 municípios do RS | Malha vigente na API do IBGE na data da coleta | Desenha no mapa os municípios das bases 2 e 3 |
| 5. Limites dos bairros | 94 bairros oficiais de Porto Alegre | Divisão da LC 12.112/2016 | Os mesmos 94 bairros do `data.json` (após 2 ajustes de grafia): colore o mapa da Tela 1 |
| 6. Cadastro de escolas | 361 escolas municipais e conveniadas de Porto Alegre | Extração de 01/01/2025 | Cada escola recebe o bairro; em cada nível, contamos as escolas em bairros atingidos |

## 3. Descrição de cada base

### 3.1 INCT SiMAI: simulação de enchentes por bairro (`data.json`)

- **Conteúdo:** para cada nível do Guaíba de 3,0 a 10,0 m (de 0,1 em 0,1 m) e cada um dos 94 bairros:
  - prédios afetados e total de prédios;
  - % afetado;
  - população;
  - população afetada.
- **Tamanho:** 6.674 registros (71 níveis × 94 bairros).
- **Recorte:** Porto Alegre. A população é a do Censo 2022 (soma 1.332.845) e os prédios vêm do OpenStreetMap. É uma simulação e não tem data de referência.
- **Qualidade:** encontramos 17 valores inconsistentes e um arredondamento para cima que infla a população afetada entre 0,8% e 5,3%. O tratamento está em `relatorios/limpeza_dados.pdf`.
- **Atenção:** a ferramenta online do INCT mostra números diferentes deste arquivo para o mesmo nível. Ver `relatorios/dashboard.pdf`, seção 7.

### 3.2 e 3.3 IBGE: dados agregados para as áreas afetadas

- **Conteúdo:** por município do RS, dentro da mancha de inundação e no total do município:
  - pessoas;
  - domicílios particulares e coletivos;
  - edificações em construção;
  - estabelecimentos agropecuários, de ensino, de saúde, religiosos e outros.
- **Origem:** o IBGE cruzou o Censo 2022 e o Cadastro Nacional de Endereços (CNEFE) com duas manchas oficiais:
  - **SPGG-RS (15/05/2024):** a mancha do Mapa Único do Plano Rio Grande (MUP), feita no pico da cheia. Tem 223 municípios e 563.432 pessoas.
  - **INPE/ANA v3 (19/06/2024):** a mancha final do governo federal. Tem 345 municípios (300 com moradores na área) e 876.564 pessoas.
- **Por que esta base e não o MUP direto:** o painel do MUP (mup.rs.gov.br) é um Power BI sem download nem API. O IBGE publicou a agregação oficial sobre a **mesma mancha**, em planilha aberta.
- **Ligação com o INCT:** Porto Alegre aparece nas duas manchas, com 122.663 e 152.258 moradores. O total de moradores de POA no IBGE (1.332.845) é **idêntico** ao do `data.json`, o que confirma a mesma base populacional.
- **Limitações:** dados por município, não por bairro. “Estabelecimento de ensino/saúde” no CNEFE inclui particulares e consultórios.

### 3.4 IBGE: malha municipal do RS

- **Conteúdo:** contorno dos 497 municípios do RS em GeoJSON (coordenadas geográficas), na qualidade “mínima” (256 KB), suficiente para um mapa do estado.
- **Ligação:** o código do município (`codarea`) é o mesmo `cod_ibge` das planilhas. O script confere que todos os municípios das planilhas têm polígono.

### 3.5 Prefeitura: limites oficiais dos bairros (LC 12.112/2016)

- **Origem:** conjunto oficial “Bairros (LC 12.112/16)”, publicado pela Secretaria do Meio Ambiente e da Sustentabilidade (SMAMS) no portal de dados abertos da Prefeitura, que tem link direto de download.
- **Mesmo arquivo do ObservaPOA:** o enunciado indica os “Bairros Oficiais” da página de mapas do ObservaPOA (<https://prefeitura.poa.br/smpae/observapoa/mapas>, shapefile `bairros_vigentes` no Google Drive). Em 24/11/2026 comparamos os dois arquivos: as mesmas 128 feições, os mesmos 94 nomes, o mesmo sistema de coordenadas (TM-POA) e diferença de área zero em todos os bairros (área total de 472,285 km² nos dois). São o mesmo dado; usamos o do portal de dados abertos porque o link de download é direto.

- **Conteúdo:** 128 polígonos, que formam os 94 bairros oficiais (o Arquipélago tem várias ilhas). Shapefile em TM-POA/SIRGAS 2000 (metros).
- **Preparação** (`scripts/preparar_prefeitura.py`):
  - normalização dos nomes (sem acento, maiúsculas, sem apóstrofo);
  - 2 ajustes de grafia (“CEL. APARICIO BORGES” e “PASSO DA AREIA”);
  - junção das partes de cada bairro;
  - simplificação (tolerância de 10 m);
  - conversão para coordenadas geográficas.

  O arquivo final tem 178 KB. O script confere que os 94 nomes são **exatamente** os do INCT.
- **Ligação:** é a mesma divisão de 94 bairros usada pelo INCT, o que permite colorir o mapa com a simulação.

### 3.6 Prefeitura: cadastro de escolas (SIE/SMED)

- **Conteúdo:** 361 escolas em atividade (99 municipais e 262 conveniadas), com tipo, endereço, bairro e coordenadas. É a extração de 01/01/2025.
- **Problemas encontrados e tratamento:**
  - **3 linhas com 42 campos em vez de 40**, por causa de `;` dentro do e-mail ou do site, que vêm **depois** da coluna de bairro. As linhas foram **recuperadas**: os campos que usamos estão no lugar certo.
  - **Rótulos trocados:** as colunas “latitude” e “longitude” trazem, na verdade, as coordenadas X/Y em TM-POA (metros).
  - **Nomes de bairro truncados** (ex.: “CENTRO HISTORIC”, “VL JOAO PESSOA”): 6 ajustes de grafia.
  - **Bairro desatualizado:** em 55 escolas, o bairro declarado não é o bairro onde o ponto cai na malha oficial. Quase sempre é a divisão anterior à lei de 2016 (ex.: escolas declaradas em “Rubem Berta” que hoje ficam em Santa Rosa de Lima). **Decisão:** usar o bairro do ponto, que segue a mesma divisão do INCT. As 38 escolas sem coordenada (0, 0) usam o bairro declarado.
- **Ligação:** junta-se à simulação pelo bairro. Em cada nível, contamos quantas escolas ficam em bairros atingidos.
- **Limitação:** não inclui escolas estaduais nem particulares sem convênio.

## 4. Coleta responsável

- Download automatizado (`scripts/coletar_ibge.py` e `scripts/preparar_prefeitura.py`) **só na primeira execução**. Depois, os arquivos brutos ficam em `dados/originais/` e não são baixados de novo.
- Antes de cada download, o script lê o `robots.txt` do site. No portal da Prefeitura, o `robots.txt` bloqueia `/api/` e pede **10 s entre requisições**: usamos só os links públicos de download e esperamos o tempo pedido.
- O servidor de API do IBGE não responde em `/robots.txt`. O script registra um aviso e segue, porque se trata de uma API pública feita para acesso automatizado.
- Cada arquivo tem URL e data registradas em `dados/originais/coleta.json`.

## 5. Bases consideradas e não usadas

| Base | Motivo |
|---|---|
| Painel do MUP (Power BI) | Sem download nem API. Usamos a agregação do IBGE sobre a mesma mancha |
| Renda por bairro (Censo 2022) | Os resultados por bairro ainda não estavam disponíveis de forma confiável |
| Série histórica do nível do Guaíba (ANA) | Fora do escopo: a simulação não tem dimensão de tempo |
| Unidades de saúde por bairro | A Tela 2 já traz saúde por município (IBGE). Priorizamos escolas, com cadastro oficial e coordenadas |
