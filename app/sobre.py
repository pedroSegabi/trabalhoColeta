"""Página de apoio: como usar, limitações, correções feitas, fontes, equipe e uso de IA."""
import streamlit as st

from dados import REPO, fontes

st.title("Como usar, limitações e fontes")

st.markdown(f"""
Painel alternativo à ferramenta de enchentes do **INCT SiMAI**, feito no Projeto Extensionista *Coleta, Preparação e
Análise de Dados* (PUCRS). Ele responde a duas perguntas: **se o Guaíba chegar a X metros, quem é afetado?**
(Tela 1) e **o que a enchente real de 2024 acrescenta?** (Tela 2).

### Como usar
- **Nível do rio:** arraste o controle (3,0 a 10,0 m, de 0,1 em 0,1 m). Tudo na tela se atualiza. O nível
  escolhido vale para as duas telas e vai para o endereço da página (`?nivel=6,5`): copie o link para mostrar um
  cenário a alguém.
- **Mapa e animação:** passe o mouse sobre um bairro para ver os números; na aba *Animação*, aperte
  *Reproduzir* para ver a água subir.
- **Consulte um bairro:** escolha um bairro para ver a partir de que nível ele começa a ser atingido.
- **Dados originais × corrigidos:** o botão *Ver dados originais do INCT* mostra os números sem as nossas
  correções, para comparar.
- **Baixe os dados:** CSV do nível escolhido ou de todos os níveis.
- **Tela 2:** escolha a mancha de inundação e o indicador; o ranking e o mapa do RS mudam juntos. A parte de
  Porto Alegre e a de escolas usam o mesmo nível da Tela 1.

### Limitações (leia antes de usar os números)
- **É uma simulação, não uma previsão nem uma contagem.** Considera só o nível do Guaíba. Chuva local, falha de
  comportas e diques e o tempo de cheia não entram.
- **Pessoas afetadas é uma estimativa:** a população de cada bairro (Censo 2022) é dividida igualmente entre todos
  os prédios, inclusive comércio e galpões. Em bairros com poucos moradores por prédio, o número é frágil.
- **Prédios** vêm do OpenStreetMap, que é mais completo em alguns bairros do que em outros.
- **O resultado é por bairro.** O painel não diz qual rua ou qual prédio alaga. Uma escola num bairro atingido
  não quer dizer que a escola alagou.
- **Os dados do IBGE são por município** e medem o que alagou de fato em 2024 (duas manchas oficiais diferentes).
  Por isso a comparação com a simulação é feita para Porto Alegre como um todo.
- **Escolas:** só a rede municipal e as conveniadas cadastradas na SMED (361). As estaduais e as particulares não
  conveniadas não estão nesse cadastro.

### O que corrigimos no arquivo do INCT
Encontramos e tratamos **17 valores inconsistentes** em 6.674 registros. Houve zeros isolados, um pico isolado,
valores maiores do que o total do bairro e a oscilação no Arquipélago. Também refizemos os percentuais **sem
arredondar para cima**: o arredondamento inflava a população afetada entre 0,8% e 5,3%. A 5,3 m, por exemplo, o
original diz 138.414 pessoas e o corrigido, 136.378. O passo a passo está no
[relatório de limpeza]({REPO}/blob/main/relatorios/limpeza_dados.pdf), que também traz a devolutiva ao INCT.

### Fontes e data de coleta
""")
fontes()

st.markdown(f"""
### Equipe e código
Pedro Ernesto, Ana Luiza Romanini, Enrico Pheula, Fransico Cassol e Pedro Fam.
Código, dados e relatórios: [{REPO.removeprefix('https://')}]({REPO}).

### Uso de IA
Usamos o Claude Code (Anthropic). **Todas as tarefas foram solicitadas pela equipe ao Claude, e todo o resultado
foi revisado pela equipe.** O registro detalhado está em `relatorios/dashboard.pdf` e `relatorios/limpeza_dados.pdf`.
""")
