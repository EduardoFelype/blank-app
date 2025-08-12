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
