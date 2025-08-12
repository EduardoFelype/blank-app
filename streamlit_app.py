# painel_validacao.py
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from io import BytesIO

st.set_page_config(page_title="Painel de Validação Prévia x Base", page_icon="📊", layout="wide")

st.title("📊 Validação Prévia x Base com SLA")

# Upload dos arquivos
st.sidebar.header("📂 Upload dos Arquivos Excel")
arquivo_previa = st.sidebar.file_uploader("Arquivo da Prévia (.xlsx)", type=["xlsx"])
arquivo_base = st.sidebar.file_uploader("Arquivo Base (.xlsx)", type=["xlsx"])

if arquivo_previa and arquivo_base:
    try:
        # Configurações
        col_circuito = "Circuito"
        col_disp_mensal = "Disponibilidade"
        col_sla_disp = "SLA disponibilidade"

        # Ler Prévia
        previa = pd.read_excel(arquivo_previa)
        previa.columns = previa.columns.str.strip()

        # Ler Base (todas as abas e concatenar)
        abas_base = pd.read_excel(arquivo_base, sheet_name=None)
        base_all = pd.concat(abas_base.values(), ignore_index=True)
        base_all.columns = base_all.columns.str.strip()

        # Colunas F e G da base (posições 5 e 6, zero-indexed)
        col_f = base_all.columns[5]
        col_g = base_all.columns[6]

        base_subset = base_all[[col_circuito, col_f, col_g]].copy()

        # Verificação SLA
        def verificar_sla(row):
            if pd.isna(row.get(col_disp_mensal)) or pd.isna(row.get(col_sla_disp)):
                return "Dados faltando"
            return "Excedido" if row[col_disp_mensal] < row[col_sla_disp] else "Não Excedido"

        previa["SLA_Status"] = previa.apply(verificar_sla, axis=1)

        # Status dos circuitos
        circuitos_previa = set(previa[col_circuito].dropna().astype(str).str.strip())
        circuitos_base = set(base_all[col_circuito].dropna().astype(str).str.strip())

        def status_circuito(circ):
            if pd.isna(circ):
                return "Circuito ausente"
            return "OK" if str(circ).strip() in circuitos_base else "Extra na Prévia"

        previa["Status_Circuito"] = previa[col_circuito].apply(status_circuito)

        faltantes_na_previa = circuitos_base - circuitos_previa
        extras_na_previa = circuitos_previa - circuitos_base

        # Merge para juntar colunas F e G na prévia
        previa_final = pd.merge(
            previa,
            base_subset,
            on=col_circuito,
            how="left",
            suffixes=("", "_Base")
        )

        # Resumo
        resumo = {
            "Total linhas prévia": len(previa_final),
            "Total linhas base (todas abas)": len(base_all),
            "SLA Excedido": (previa_final["SLA_Status"] == "Excedido").sum(),
            "SLA Não Excedido": (previa_final["SLA_Status"] == "Não Excedido").sum(),
            "SLA Dados faltando/erro": (~previa_final["SLA_Status"].isin(["Excedido", "Não Excedido"])).sum(),
            "Circuitos extras na prévia": len(extras_na_previa),
            "Circuitos faltando na prévia": len(faltantes_na_previa)
        }

        # Mostrar resumo com métricas lado a lado
        st.subheader("📈 Resumo Geral")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total linhas Prévia", resumo["Total linhas prévia"])
        col2.metric("Total linhas Base", resumo["Total linhas base (todas abas)"])
        col3.metric("SLA Excedido", resumo["SLA Excedido"])
        col4.metric("SLA Não Excedido", resumo["SLA Não Excedido"])

        col5, col6 = st.columns(2)
        col5.metric("SLA Dados faltando/erro", resumo["SLA Dados faltando/erro"])
        col6.metric("Circuitos extras na Prévia", resumo["Circuitos extras na prévia"])

        st.metric("Circuitos faltando na Prévia", resumo["Circuitos faltando na prévia"])

               

        fig_bar, ax_bar = plt.subplots()
        ax_bar.bar(status_counts.index, status_counts.values, color=["#118ab2", "#ef476f", "#ffd166"])
        ax_bar.set_ylabel("Quantidade")
        ax_bar.set_xlabel("Status do Circuito")
        ax_bar.set_title("Comparação dos Circuitos entre Prévia e Base")

                # Gráfico de barras para SLA_Status
        st.subheader("📊 SLA Excedido vs Não Excedido")
        fig_bar_sla, ax_bar_sla = plt.subplots()
        sla_counts = previa_final["SLA_Status"].value_counts()

        ax_bar_sla.barh(sla_counts.index, sla_counts.values, color=["#ef476f", "#06d6a0", "#ffd166"])
        ax_bar_sla.set_xlabel("Quantidade")
        ax_bar_sla.set_ylabel("Status SLA")
        ax_bar_sla.set_title("Comparação de SLA")
        
        # Adiciona os valores no final de cada barra
        for i, v in enumerate(sla_counts.values):
            ax_bar_sla.text(v + 0.5, i, str(v), va='center', fontweight='bold')

        st.pyplot(fig_bar_sla)


        # Adiciona valores no topo das barras
        for i, v in enumerate(status_counts.values):
            ax_bar.text(i, v + 0.5, str(v), ha='center', fontweight='bold')

        st.pyplot(fig_bar)

# Gráfico de barras para status dos circuitos
        st.subheader("📊 Status dos Circuitos (Comparação Prévia x Base)")
        status_counts = previa_final["Status_Circuito"].value_counts()
        
        # Mostrar circuitos extras e faltantes
        st.subheader("⚠️ Circuitos Extras na Prévia")
        if extras_na_previa:
            st.write(sorted(list(extras_na_previa)))
        else:
            st.write("Nenhum circuito extra.")

        st.subheader("⚠️ Circuitos Faltando na Prévia")
        if faltantes_na_previa:
            st.write(sorted(list(faltantes_na_previa)))
        else:
            st.write("Nenhum circuito faltando.")

        # Mostrar tabela completa
        st.subheader("📋 Dados Completos (Prévia + Base)")
        st.dataframe(previa_final)

        # Botão para download Excel
        def to_excel(df):
            output = BytesIO()
            writer = pd.ExcelWriter(output, engine='openpyxl')
            df.to_excel(writer, index=False)
            writer.save()
            processed_data = output.getvalue()
            return processed_data

        excel_data = to_excel(previa_final)

        st.download_button(
            label="💾 Baixar arquivo Excel com resultado",
            data=excel_data,
            file_name="validacao_completa.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"❌ Ocorreu um erro: {e}")

else:
    st.info("⏳ Por favor, envie os dois arquivos Excel para começar a validação.")