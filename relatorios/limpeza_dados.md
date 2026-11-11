# Relatório de Limpeza de Dados: Fase 2

**Projeto Extensionista: Análise de Dados de Enchentes do INCT SiMAI**

Coleta, Preparação e Análise de Dados (PUCRS), Profª Katherine Bianchini Esper de Vargas

**Equipe:** Pedro Ernesto, Ana Luiza Romanini, Enrico Pheula, Fransico Cassol, Pedro Fam

**Data:** 10/11/2026

---

## 1. Objetivo

Este relatório documenta a preparação das duas bases usadas no dashboard:

1. o arquivo `data.json` do INCT SiMAI, com a simulação de prédios alagados por bairro de Porto Alegre para níveis do Guaíba de 3,0 m a 10,0 m (Tela 1);
2. a base externa do IBGE com pessoas, domicílios e estabelecimentos na área alagada em 2024, por município do RS (Tela 2).

Para cada inconsistência encontrada no `data.json`, registramos **onde ela aparece, por que é um problema e como foi tratada**, conforme pede o enunciado. A seção 6 resume os achados para envio ao INCT como devolutiva.

## 2. Fontes de dados

| Base | Origem | Formato | Forma de coleta | Data de coleta | Uso |
|---|---|---|---|---|---|
| Simulação de enchentes por bairro | INCT SiMAI (arquivo `data.json` distribuído no Moodle) | JSON | Arquivo fornecido | 10/11/2026 | Tela 1 |
| Dados agregados para as áreas afetadas: mancha SPGG-RS de 15/05/2024 (a mesma do Mapa Único do Plano Rio Grande, MUP) | IBGE ([FTP apoio_rs](https://ftp.ibge.gov.br/Informacoes_Gerais_e_Referencia/SINGED_Lab/apoio_rs/Solicitacoes_especiais/08_Secretaria_de_Plan_Gov_e_Gestao_do_RS/)) | XLSX | Download automatizado (`scripts/coletar_ibge.py`) | 10/11/2026 | Tela 2 |
| Dados agregados para as áreas afetadas: mancha v3 INPE/ANA de 19/06/2024 | IBGE ([FTP apoio_rs](https://ftp.ibge.gov.br/Informacoes_Gerais_e_Referencia/SINGED_Lab/apoio_rs/Dados_agregados_para_toda_a_area_afetada_v3_Governo_Federal/)) | XLSX | Download automatizado (`scripts/coletar_ibge.py`) | 10/11/2026 | Tela 2 |

## 3. Base INCT (`data.json`)

### 3.1 Estrutura e checagens

O arquivo foi carregado no formato longo com o código do enunciado, que lê **por chave** e não por posição (`scripts/limpar_inct.py`). As checagens a seguir rodam como `assert` no script, e todas passaram:

| Checagem | Resultado |
|---|---|
| Dimensão do formato longo | 6.674 linhas × 7 colunas (71 níveis × 94 bairros) |
| Níveis de 3,0 a 10,0 m em passos de 0,1 m, sem falhas nem duplicatas | OK |
| 94 bairros em todos os níveis, sem nomes duplicados nem variações de grafia | OK |
| Campos presentes em todas as linhas, todos inteiros, sem nulos | OK |
| `total_buildings` e `population` constantes por bairro em todos os níveis | OK |
| Soma de `population` em cada nível | 1.332.845 = população de Porto Alegre no Censo 2022 (confere com o IBGE) |

As checagens de **conteúdo** usaram duas regras:

- **Regra física:** quando o rio sobe, o número de prédios afetados de um bairro **nunca pode diminuir**. Encontramos 12 quedas em 5 bairros.
- **Regra de cálculo:** `percentage` deveria ser 100 × `affected_buildings` / `total_buildings`, e `affected_population` deveria ser `population` × `percentage` / 100. As duas fórmulas foram testadas linha a linha.

### 3.2 Inconsistências encontradas e tratamento

#### I1. Zeros isolados no meio da série

| Bairro | Nível | Valor no arquivo | Vizinhos | Valor corrigido |
|---|---|---|---|---|
| Centro Histórico | 9,7 m | 0 | 2.050 (9,6 m) e 2.130 (9,9 m) | 2.077 |
| Centro Histórico | 9,8 m | 0 | 2.050 (9,6 m) e 2.130 (9,9 m) | 2.103 |
| Lageado | 8,1 m | 0 | 108 (8,0 m) e 110 (8,2 m) | 109 |
| Rubem Berta | 8,8 m | 0 | 252 (8,7 m) e 285 (8,9 m) | 268 |

- **Por que é um problema.** Um bairro com 2.050 prédios alagados não pode ficar seco com o rio 10 cm mais alto. Também zeram `percentage` e `affected_population`, o que tira **~14,7 mil pessoas** do total da cidade a 9,7 m e 9,8 m e faz o Centro Histórico sumir do ranking.
- **Decisão: interpolar.** É claramente uma falha de registro, e os vizinhos imediatos estão disponíveis e coerentes. A interpolação linear pelo nível é a estimativa mais conservadora.

#### I2. Pico isolado: Espírito Santo a 4,7 m

- **Onde.** 2.101 prédios afetados (63%) a 4,7 m, entre 46 (4,6 m) e 47 (4,8 m).
- **Por que é um problema.** Um salto de 45 vezes, que desaparece no nível seguinte. Ele infla a cidade em **~3 mil pessoas** a 4,7 m e coloca o bairro no topo do ranking de forma indevida.
- **Decisão: interpolar** (valor corrigido: 46).

#### I3. Início impossível: Espírito Santo de 3,0 a 3,4 m

- **Onde.** 637 prédios (3,0 a 3,3 m) e 633 (3,4 m). A série cai para 25 em 3,5 m e só chega a 133 em 10 m.
- **Por que é um problema.** O bairro teria mais prédios alagados a 3,0 m do que a 10 m. Isso viola a regra física em todos os níveis seguintes.
- **Decisão: corrigir com o valor de 3,5 m (25).** Não há vizinho anterior para interpolar. Como o valor a 3,0–3,4 m não pode ser maior que o de 3,5 m, usar 25 é o limite superior compatível com a física. Os 5 valores ficam sinalizados na coluna `correcao`.

#### I4. Oscilação no Arquipélago

- **Onde.** O bairro tem 4.688 prédios e aparece com **4.680 afetados em 64 dos 71 níveis**. Os desvios são 4.685 em 3,0 / 3,5 / 4,0 / 4,5 / 5,0 m, 4.688 em 5,3 m e 4.674 em 4,1 m.
- **Por que é um problema.** São quedas pequenas (≤ 14 prédios, ≤ 0,3%), mas que violam a regra física. Seis dos sete desvios caem exatamente nos níveis com estrutura diferente (ver I8). Só o de 4,1 m fica fora desse grupo.
- **Decisão: usar o valor modal (4.680) em todos os níveis.** É o valor da grande maioria dos níveis, e os desvios vêm quase todos do lote suspeito. Assim mudam só 7 valores, e o impacto é desprezível: o bairro continua ~99,8% atingido, com variação de até 11 pessoas.

#### I5. `percentage` arredondada sempre para cima

- **Onde.** Em **todas as 6.674 linhas**, `percentage` = teto((afetados / total) × 100), um inteiro arredondado para cima. Exemplo: Santa Rosa de Lima a 3,0 m tem 11 prédios afetados de 12.870 (0,085%), e o arquivo registra **1%**.
- **Por que é um problema.** Superestima sistematicamente os bairros pouco atingidos e esconde diferenças menores que 1 ponto percentual.
- **Decisão: recalcular** como 100 × `affected_buildings` / `total_buildings`, com 2 casas decimais. O valor original fica na coluna `percentage_orig`.

#### I6. Erro de ponto flutuante no teto: Boa Vista do Sul a 7,2 e 7,3 m

- **Onde.** `percentage` = 29, mas 686 / 2.450 = **28%** exatos.
- **Por que é um problema.** Em ponto flutuante, (686 / 2450) × 100 dá 28,000000000000004, e o teto desse valor vira 29. Mesmo um percentual exato acaba "arredondado para cima" e fica errado. É uma consequência direta de aplicar o teto (I5) a um número de ponto flutuante.
- **Decisão.** Resolvido pelo recálculo de I5.

#### I7. `affected_population` herda o arredondamento

- **Onde.** Em **todas as 6.674 linhas**, `affected_population` = teto(`population` × `percentage` / 100), calculada a partir do percentual inteiro já arredondado para cima. Santa Rosa de Lima a 3,0 m aparece com **347 pessoas afetadas, quando o cálculo exato dá 30**. O valor também fica "travado" em degraus: no Centro Histórico, ele é 612 de 3,1 a 3,5 m, enquanto os prédios afetados vão de 44 a 78.
- **Por que é um problema.** Infla a população afetada da cidade em **+1,3 mil a +4,0 mil pessoas por nível**, entre **+0,8% e +5,3%** conforme o nível: +4,8% a 3,0 m, +1,5% a 5,3 m e +1,1% a 10 m.
- **Decisão: recalcular** como `population` × `affected_buildings` / `total_buildings`, arredondado para o inteiro mais próximo. O valor original fica em `affected_population_orig`.

#### I8. Estrutura heterogênea entre níveis

- **Onde.** Os níveis **3,0 / 3,5 / 4,0 / 4,5 / 5,0 / 5,3 m** têm os campos em outra ordem (`affected_buildings` primeiro) em relação aos outros 65 níveis. No nível 5,3 m, os bairros também estão em outra ordem (Morro Santana deslocado para o fim da lista).
- **Por que é um problema.** Quem lê o arquivo por posição, e não por chave, atribui valores ao bairro ou campo errado. A coincidência com os valores anômalos do Arquipélago (I4) indica que o arquivo junta **dois lotes de simulação** diferentes.
- **Decisão: manter e avisar.** A leitura por chave torna o problema inofensivo para o nosso processamento. O achado é registrado para o INCT verificar se os dois lotes usaram os mesmos parâmetros.

#### I9. Limitações do método (não são erros)

- A população afetada supõe **distribuição uniforme dos moradores entre todos os prédios**, inclusive os não residenciais (galpões, comércio). Em bairros com muitos prédios e poucos moradores, como São Caetano (733 habitantes, 940 prédios, 0,78 hab./prédio), a estimativa é frágil.
- `total_buildings` vem do OpenStreetMap, cuja cobertura varia entre bairros.
- 40 dos 94 bairros nunca são atingidos, nem a 10 m. É um resultado esperado, porque são bairros altos.

**Decisão: manter e avisar.** Essas limitações aparecem no aviso obrigatório do dashboard.

### 3.3 Impacto da limpeza nos totais da cidade

| Nível | Prédios afetados (original) | Prédios afetados (limpo) | Pessoas afetadas (original) | Pessoas afetadas (limpo) | Diferença |
|---|---|---|---|---|---|
| 3,0 m | 15.264 | 14.647 | 34.605 | 32.112 | −2.493 |
| 4,0 m | 32.781 | 32.776 | 84.970 | 83.097 | −1.873 |
| 4,7 m | 47.521 | 45.466 | 120.271 | 115.020 | −5.251 |
| 5,0 m | 49.628 | 49.623 | 127.611 | 125.692 | −1.919 |
| **5,3 m** | **53.989** | **53.981** | **138.414** | **136.378** | **−2.036** |
| 6,0 m | 64.486 | 64.486 | 165.811 | 163.825 | −1.986 |
| 8,0 m | 83.009 | 83.009 | 221.899 | 218.349 | −3.550 |
| 9,7 m | 96.273 | 98.350 | 252.080 | 263.699 | +11.619 |
| 10,0 m | 101.211 | 101.211 | 274.993 | 271.875 | −3.118 |

Na maioria dos níveis, a limpeza **reduz** a população afetada em ~2 mil pessoas, porque remove o arredondamento para cima. A 9,7 m, ela **aumenta** o total ao devolver o Centro Histórico, que tinha sido zerado por engano. Depois da limpeza, a curva da cidade é estritamente crescente.

### 3.4 Resultado

`dados/processados/inct_limpo.json`: formato longo (6.674 registros), com as colunas:

- `nivel_m`, `bairro`, `affected_buildings`, `total_buildings`, `percentage`, `population`, `affected_population`: os valores **limpos**;
- `affected_buildings_orig`, `percentage_orig`, `affected_population_orig`: os valores **originais**, para rastreabilidade;
- `correcao`: o tipo de correção aplicada à linha (vazio quando não houve).

`dados/processados/inct_correcoes.csv` lista os **17 valores** de `affected_buildings` alterados: 10 dos itens I1–I3 e 7 do Arquipélago (I4). Cada um traz valor original, valor novo, método e motivo.

## 4. Base externa: IBGE sobre as manchas de 2024 (MUP / INPE-ANA)

### 4.1 Por que não usar diretamente o painel do MUP

O Mapa Único do Plano Rio Grande (mup.rs.gov.br), escolhido na Fase 1, é um **painel Power BI incorporado**, sem opção de download nem API pública. Extrair dados do Power BI exigiria contornar o mecanismo de acesso do site, o que contraria a orientação de coleta responsável. A mesma mancha de inundação da SPGG-RS (a secretaria responsável pelo MUP) foi cruzada pelo **IBGE** com o Censo 2022 e o CNEFE, e o resultado foi **publicado em planilha aberta**. Usamos essa publicação oficial e a versão final da mancha (v3, INPE/ANA).

### 4.2 Coleta

`scripts/coletar_ibge.py`:

1. consulta o `robots.txt` do servidor, que hoje não existe (HTTP 404), o que significa que não há restrições;
2. baixa as duas planilhas com `requests`, **apenas se ainda não existirem** em `dados/originais/`, para não repetir requisições;
3. guarda a data de download em `dados/originais/coleta_ibge.json`, porque o git não preserva a data dos arquivos e um clone teria a data errada, e copia a URL de origem e a data de coleta para cada linha (colunas `fonte_url` e `data_coleta`).

### 4.3 Preparação

- A planilha tem **cabeçalho em duas linhas** (grupo "Áreas afetadas / Total do município / % áreas afetadas" + nome do indicador). O cabeçalho foi achatado em nomes únicos, como `pessoas_afetados` e `pessoas_total`.
- Foram descartadas as linhas sem código de município: 1 ou 2 linhas em branco e a nota de rodapé com as siglas. Restaram **223 municípios** na mancha SPGG/MUP e **345** na INPE/ANA.
- As colunas de percentual da planilha foram ignoradas. O percentual de pessoas afetadas é **recalculado** a partir das contagens, para não repetir o problema de arredondamento visto no INCT.
- As duas manchas foram empilhadas em **formato longo** (uma linha por município × mancha) em `dados/processados/ibge_areas_afetadas.csv`.

### 4.4 Checagens

Todas rodam como `assert` no script, e todas passaram:

- Porto Alegre = **122.663** pessoas (SPGG/MUP) e **152.258** (INPE/ANA), conferindo com os ofícios do IBGE;
- a população total de Porto Alegre na planilha (1.332.845) é igual à soma de `population` do `data.json` do INCT, o que confirma que as duas bases usam o mesmo Censo;
- não há município repetido dentro da mesma mancha;
- em todos os indicadores, os afetados são menores ou iguais ao total do município.

### 4.5 Limitações

- **Escala:** os dados são por **município**, não por bairro. A ligação com a Tela 1 é feita por Porto Alegre como um todo e pela enchente de 2024.
- **Natureza diferente:** a mancha é o que alagou de fato, incluindo chuva, falhas de diques e comportas e o Delta do Jacuí. A simulação do INCT considera apenas o nível do Guaíba. O IBGE conta **moradores**, enquanto o INCT **estima** pessoas por prédio.
- **Datas:** a mancha SPGG de 15/05/2024 era preliminar e não inclui o sul do estado (Rio Grande, Pelotas), que alagou depois.
- **CNEFE:** "estabelecimento de ensino/saúde" é o endereço cadastrado com essa finalidade, o que inclui consultórios e escolas particulares, e não apenas a rede pública.

## 5. Reprodutibilidade

Todo o processamento é feito por scripts Python versionados no repositório. Os passos para reproduzir dados, notebook, wireframes e este PDF estão na seção **"Como rodar"** do `README.md`.

## 6. Devolutiva ao INCT (resumo)

1. Zeros isolados em Centro Histórico (9,7 e 9,8 m), Lageado (8,1 m) e Rubem Berta (8,8 m).
2. Valores espúrios no Espírito Santo: 637/633 prédios de 3,0 a 3,4 m e 2.101 a 4,7 m.
3. Oscilação de prédios afetados no Arquipélago (4.680 em 64 níveis; desvios em 7 níveis, 6 deles os do item 6).
4. `percentage` armazenada como inteiro arredondado para cima, e `affected_population` calculada a partir dela, o que infla a população afetada entre 0,8% e 5,3% por nível. Sugestão: armazenar a fração exata.
5. Como o teto é aplicado a um valor de ponto flutuante, Boa Vista do Sul a 7,2 e 7,3 m fica com 29%, quando 686/2.450 é exatamente 28%.
6. Níveis 3,0 / 3,5 / 4,0 / 4,5 / 5,0 / 5,3 m com estrutura diferente dos demais, o que sugere dois lotes de simulação. Vale verificar se usaram os mesmos parâmetros.

## 7. Uso de ferramentas de IA

Conforme as regras da disciplina, registramos o uso de IA nesta fase. A ferramenta usada foi o **Claude Code (Anthropic)**. **Todas as tarefas abaixo foram solicitadas pela equipe ao Claude, e todo o resultado (código, gráficos e textos) foi revisado pela equipe** antes da entrega.

| Etapa | O que a equipe pediu ao Claude |
|---|---|
| Auditoria do `data.json` | Sugerir e executar testes de consistência (monotonicidade, fórmulas, estrutura) |
| Scripts de coleta e limpeza | Escrever `coletar_ibge.py`, `limpar_inct.py`, `wireframe.py` e `gerar_pdf.py` |
| Notebook de EDA | Gerar os gráficos e o rascunho dos comentários |
| Este relatório | Redigir o texto a partir das saídas dos scripts |
| Revisão de código | Revisar o código e os textos (`/code-review`). A revisão apontou erros que foram corrigidos, entre eles o diagnóstico do I6 e a correção do Arquipélago (I4) |

A escolha das bases, as decisões de tratamento (seção 3.2) e a validação dos resultados foram feitas pela equipe. Todos os membros revisaram o código e conseguem explicá-lo.
