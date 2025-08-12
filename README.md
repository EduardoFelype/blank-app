# 📊 Painel de Validação Prévia x Base com SLA

Este projeto é um **painel interativo em Streamlit** para comparar dois arquivos Excel — um da **Prévia** e outro da **Base** — verificando se os circuitos atendem ao **SLA de disponibilidade** e identificando diferenças entre as listas.

## 🚀 Funcionalidades

- 📂 Upload de dois arquivos Excel (Prévia e Base)
- 📈 Resumo de métricas gerais:
  - Total de linhas na Prévia e na Base
  - Quantidade de circuitos com SLA **Excedido** ou **Não Excedido**
  - Circuitos extras ou faltantes na Prévia
- 📊 Visualizações gráficas:
  - Distribuição de **SLA Excedido / Não Excedido / Dados faltando** (Pizza e/ou Barras)
- 📋 Tabela consolidada com dados da Prévia e colunas da Base
- 💾 Opção para download do resultado em Excel

---

## 🛠️ Instalação

1. Clone este repositório:

```bash
git clone https://github.com/seu-usuario/seu-repositorio.git
cd seu-repositorio

Crie e ative um ambiente virtual (opcional, mas recomendado):

python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

Instale as dependências:

pip install streamlit pandas openpyxl matplotlib

▶️ Execução

Para rodar o painel localmente:
streamlit run painel_validacao.py
O Streamlit abrirá o painel no seu navegador (geralmente em http://localhost:8501).

📄 Estrutura esperada dos arquivos
Arquivo da Prévia
Colunas obrigatórias:

Circuito

Disponibilidade

SLA disponibilidade

Arquivo Base
Pode conter múltiplas abas (todas serão consolidadas).

Colunas obrigatórias:

Circuito

Colunas F e G (quaisquer nomes, serão extraídas pela posição).

📷 Exemplo de uso
Faça upload do arquivo da Prévia.

Faça upload do arquivo Base.

Veja:

Métricas resumidas.

Gráficos de distribuição.

Listas de circuitos extras/faltantes.

Baixe o resultado consolidado em Excel.

📌 Tecnologias usadas
Python 3.11+

Streamlit

Pandas

OpenPyXL

Matplotlib
