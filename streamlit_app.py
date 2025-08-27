import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Configuração da página
st.set_page_config(
    page_title="Painel de Validação Prévia x Base", 
    page_icon="📊", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para melhorar a aparência
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #7084b3;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #667eea;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Título principal
st.markdown("<div class=\"main-header\"><h1>📊 Painel de Validação Prévia x Base com SLA</h1></div>", unsafe_allow_html=True)

# Criação das abas
tab1, tab2 = st.tabs(["🔍 Validação SLA", "💰 Faturamento"])

# Variável global para armazenar dados processados
dados_processados = None

with tab1:
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
            col_valor_contratado = "Valor Contratado"

            # Ler Prévia
            previa = pd.read_excel(arquivo_previa)
            previa.columns = previa.columns.str.strip()

            # Garantir que as colunas de porcentagem sejam tratadas como decimais
            for col in [col_disp_mensal, col_sla_disp]:
                if col in previa.columns:
                    previa[col] = pd.to_numeric(previa[col], errors='coerce')
                    if (previa[col] > 1).any():
                        previa[col] = previa[col] / 100

            # Ler Base (todas as abas e concatenar)
            abas_base = pd.read_excel(arquivo_base, sheet_name=None)
            base_all = pd.concat(abas_base.values(), ignore_index=True)
            base_all.columns = base_all.columns.str.strip()

            # Colunas F e G da base (posições 5 e 6, zero-indexed)
            base_cols_to_merge = [col_circuito, base_all.columns[5], base_all.columns[6]]
            if col_valor_contratado in base_all.columns:
                base_cols_to_merge.append(col_valor_contratado)

            base_subset = base_all[base_cols_to_merge].copy()

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

            # Merge para juntar colunas F, G e Valor Contratado na prévia
            previa_final = pd.merge(
                previa,
                base_subset,
                on=col_circuito,
                how="left",
                suffixes=("", "_Base")
            )

            # Calcular Penalidade
            previa_final["Valor Contratado"] = pd.to_numeric(previa_final["Valor Contratado"], errors='coerce')
            previa_final["Penalidade"] = 0.0

            # Aplica a fórmula apenas quando o SLA for excedido
            condicao_sla_excedido = (previa_final["SLA_Status"] == "Excedido") & \
                                   (previa_final[col_valor_contratado].notna()) & \
                                   (previa_final[col_disp_mensal].notna())

            previa_final.loc[condicao_sla_excedido, "Penalidade"] = \
                (previa_final[col_valor_contratado] * previa_final[col_disp_mensal]) - previa_final[col_valor_contratado]

            # Cálculo adicional de desconto (novo)
            previa_final["Desconto_Alternativo"] = 0.0
            # Fórmula alternativa: (1 - disponibilidade) * valor_contratado
            condicao_desconto = (previa_final["SLA_Status"] == "Excedido") & \
                               (previa_final[col_valor_contratado].notna()) & \
                               (previa_final[col_disp_mensal].notna())
            
            previa_final.loc[condicao_desconto, "Desconto_Alternativo"] = \
                (1 - previa_final[col_disp_mensal]) * previa_final[col_valor_contratado]

            # Armazenar dados processados para usar na aba de faturamento
            dados_processados = previa_final.copy()

            # Resumo
            resumo = {
                "Total linhas prévia": len(previa_final),
                "Total linhas base (todas abas)": len(base_all),
                "SLA Excedido": (previa_final["SLA_Status"] == "Excedido").sum(),
                "SLA Não Excedido": (previa_final["SLA_Status"] == "Não Excedido").sum(),
                "SLA Dados faltando/erro": (~previa_final["SLA_Status"].isin(["Excedido", "Não Excedido"])).sum(),
                "Circuitos extras na prévia": len(extras_na_previa),
                "Circuitos faltando na prévia": len(faltantes_na_previa),
                "Total Penalidade Calculada": previa_final["Penalidade"].sum(),
                "Total Desconto Alternativo": previa_final["Desconto_Alternativo"].sum()
            }

            # Mostrar resumo com métricas melhoradas
            st.subheader("📈 Resumo Geral")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(
                    "Total linhas Prévia", 
                    resumo["Total linhas prévia"],
                    help="Número total de registros na prévia"
                )
            with col2:
                st.metric(
                    "Total linhas Base", 
                    resumo["Total linhas base (todas abas)"],
                    help="Número total de registros na base"
                )
            with col3:
                st.metric(
                    "SLA Excedido", 
                    resumo["SLA Excedido"],
                    delta=f"-{resumo['SLA Excedido']} problemas",
                    delta_color="inverse"
                )
            with col4:
                st.metric(
                    "SLA Não Excedido", 
                    resumo["SLA Não Excedido"],
                    delta=f"+{resumo['SLA Não Excedido']} OK",
                    delta_color="normal"
                )

            col5, col6, col7 = st.columns(3)
            with col5:
                st.metric("SLA Dados faltando/erro", resumo["SLA Dados faltando/erro"])
            with col6:
                st.metric("Circuitos extras na Prévia", resumo["Circuitos extras na prévia"])
            with col7:
                st.metric("Circuitos faltando na Prévia", resumo["Circuitos faltando na prévia"])

            # Métricas financeiras
            col8, col9 = st.columns(2)
            with col8:
                st.metric(
                    "Total Penalidade Calculada", 
                    f"R$ {resumo['Total Penalidade Calculada']:,.2f}",
                    help="Cálculo: (Valor Contratado × Disponibilidade) - Valor Contratado"
                )
            with col9:
                st.metric(
                    "Total Desconto Alternativo", 
                    f"R$ {resumo['Total Desconto Alternativo']:,.2f}",
                    help="Cálculo: (1 - Disponibilidade) × Valor Contratado"
                )

            # Gráficos melhorados com Plotly
            st.subheader("📊 Visualizações")
            
            # Gráfico 1: Status dos Circuitos (Pizza)
            col_graf1, col_graf2 = st.columns(2)
            
            with col_graf1:
                st.markdown("**Status dos Circuitos**")
                status_counts = previa_final["Status_Circuito"].value_counts()
                
                fig_pie = px.pie(
                    values=status_counts.values,
                    names=status_counts.index,
                    color_discrete_sequence=['#2E8B57', '#FF6B6B', '#FFD93D'],
                    title="Distribuição dos Status dos Circuitos"
                )
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                fig_pie.update_layout(height=400)
                st.plotly_chart(fig_pie, use_container_width=True)

            # Gráfico 2: SLA Status (Barras)
            with col_graf2:
                st.markdown("**Status do SLA**")
                sla_counts = previa_final["SLA_Status"].value_counts()
                
                fig_bar = px.bar(
                    x=sla_counts.index,
                    y=sla_counts.values,
                    color=sla_counts.index,
                    color_discrete_map={
                        'Não Excedido': '#2E8B57',
                        'Excedido': '#FF6B6B',
                        'Dados faltando': '#FFD93D'
                    },
                    title="Status do SLA por Quantidade"
                )
                fig_bar.update_layout(showlegend=False, height=400)
                fig_bar.update_traces(texttemplate='%{y}', textposition='outside')
                st.plotly_chart(fig_bar, use_container_width=True)

            # Gráfico 3: Comparação de Penalidades
            if resumo["SLA Excedido"] > 0:
                st.markdown("**Comparação dos Cálculos de Desconto**")
                
                penalidades_df = pd.DataFrame({
                    'Tipo de Cálculo': ['Penalidade Original', 'Desconto Alternativo'],
                    'Valor': [resumo['Total Penalidade Calculada'], resumo['Total Desconto Alternativo']]
                })
                
                fig_comp = px.bar(
                    penalidades_df,
                    x='Tipo de Cálculo',
                    y='Valor',
                    color='Tipo de Cálculo',
                    color_discrete_sequence=['#667eea', '#764ba2'],
                    title="Comparação entre Métodos de Cálculo de Desconto"
                )
                fig_comp.update_traces(texttemplate='R$ %{y:,.2f}', textposition='outside')
                fig_comp.update_layout(showlegend=False, height=400)
                st.plotly_chart(fig_comp, use_container_width=True)

            # Mostrar circuitos extras e faltantes
            col_extra, col_faltante = st.columns(2)
            
            with col_extra:
                st.subheader("⚠️ Circuitos Extras na Prévia")
                if extras_na_previa:
                    st.write(sorted(list(extras_na_previa)))
                else:
                    st.success("✅ Nenhum circuito extra.")

            with col_faltante:
                st.subheader("⚠️ Circuitos Faltando na Prévia")
                if faltantes_na_previa:
                    st.write(sorted(list(faltantes_na_previa)))
                else:
                    st.success("✅ Nenhum circuito faltando.")

            # Mostrar tabela completa
            st.subheader("📋 Dados Completos (Prévia + Base)")
            
            # Formatar colunas para exibição
            df_display = previa_final.copy()
            for col in [col_disp_mensal, col_sla_disp]:
                if col in df_display.columns:
                    df_display[col] = df_display[col].apply(lambda x: f"{x:.2%}" if pd.notna(x) else x)
            
            df_display["Penalidade"] = df_display["Penalidade"].apply(lambda x: f"R$ {x:,.2f}" if pd.notna(x) else x)
            df_display["Desconto_Alternativo"] = df_display["Desconto_Alternativo"].apply(lambda x: f"R$ {x:,.2f}" if pd.notna(x) else x)

            st.dataframe(df_display, use_container_width=True)

            # Botão para download Excel
            def to_excel(df):
                output = BytesIO()
                writer = pd.ExcelWriter(output, engine='openpyxl')
                df.to_excel(writer, index=False, sheet_name='Validacao_Completa')
                writer.close()
                processed_data = output.getvalue()
                return processed_data

            excel_data = to_excel(previa_final)

            st.download_button(
                label="💾 Baixar arquivo Excel com resultado",
                data=excel_data,
                file_name="validacao_completa_melhorada.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        except Exception as e:
            st.error(f"❌ Ocorreu um erro: {e}")
            st.exception(e)

    else:
        st.info("⏳ Por favor, envie os dois arquivos Excel para começar a validação.")

# Aba de Faturamento
with tab2:
    st.header("💰 Planilha de Faturamento Pronto")
    
    # Verificar se há dados processados da aba anterior
    if dados_processados is not None:
        try:
            # Criar planilha de faturamento baseada nos dados processados
            df_faturamento = dados_processados.copy()
            
            # Selecionar e renomear colunas para o formato de faturamento
            colunas_faturamento = {
                'Circuito': 'Circuito',
                'Valor Contratado': 'Valor Contratado',
                'Disponibilidade': 'Disponibilidade',
                'SLA disponibilidade': 'SLA Disponibilidade',
                'Penalidade': 'Penalidade',
                'Desconto_Alternativo': 'Desconto Alternativo'
            }
            
            # Filtrar apenas as colunas necessárias
            df_faturamento_final = pd.DataFrame()
            for col_original, col_nova in colunas_faturamento.items():
                if col_original in df_faturamento.columns:
                    df_faturamento_final[col_nova] = df_faturamento[col_original]
            
            # Calcular Valor Final (Valor Contratado + Penalidade)
            if 'Valor Contratado' in df_faturamento_final.columns and 'Penalidade' in df_faturamento_final.columns:
                df_faturamento_final['Valor Final'] = df_faturamento_final['Valor Contratado'] + df_faturamento_final['Penalidade']
            
            # Adicionar cabeçalho da planilha (como no exemplo)
            import datetime
            mes_atual = datetime.datetime.now().strftime("%B de %Y")
            
            st.markdown(f"### 📋 Planilha de faturamento referente aos serviços prestados em {mes_atual}")
            
            # Métricas de resumo
            col1, col2, col3, col4 = st.columns(4)
            
            total_valor_contratado = df_faturamento_final['Valor Contratado'].sum() if 'Valor Contratado' in df_faturamento_final.columns else 0
            total_penalidade = df_faturamento_final['Penalidade'].sum() if 'Penalidade' in df_faturamento_final.columns else 0
            total_desconto_alternativo = df_faturamento_final['Desconto Alternativo'].sum() if 'Desconto Alternativo' in df_faturamento_final.columns else 0
            total_valor_final = df_faturamento_final['Valor Final'].sum() if 'Valor Final' in df_faturamento_final.columns else 0
            
            with col1:
                st.metric("💰 Total Valor Contratado", f"R$ {total_valor_contratado:,.2f}")
            with col2:
                st.metric("⚠️ Total Penalidade", f"R$ {total_penalidade:,.2f}")
            with col3:
                st.metric("🔄 Total Desconto Alternativo", f"R$ {total_desconto_alternativo:,.2f}")
            with col4:
                st.metric("✅ Total Valor Final", f"R$ {total_valor_final:,.2f}")
            
            # Gráficos de faturamento
            st.subheader("📊 Visualizações do Faturamento")
            
            col_graf1, col_graf2 = st.columns(2)
            
            with col_graf1:
                # Gráfico de comparação entre métodos de desconto
                if total_penalidade != 0 or total_desconto_alternativo != 0:
                    comparacao_df = pd.DataFrame({
                        'Método': ['Penalidade Original', 'Desconto Alternativo'],
                        'Valor': [abs(total_penalidade), abs(total_desconto_alternativo)]
                    })
                    
                    fig_comp = px.bar(
                        comparacao_df,
                        x='Método',
                        y='Valor',
                        color='Método',
                        color_discrete_sequence=['#FF6B6B', '#4ECDC4'],
                        title="Comparação dos Métodos de Desconto"
                    )
                    fig_comp.update_traces(texttemplate='R$ %{y:,.0f}', textposition='outside')
                    fig_comp.update_layout(showlegend=False, height=400)
                    st.plotly_chart(fig_comp, use_container_width=True)
            
            with col_graf2:
                # Gráfico de distribuição de valores
                if 'Valor Contratado' in df_faturamento_final.columns:
                    fig_hist = px.histogram(
                        df_faturamento_final,
                        x='Valor Contratado',
                        nbins=20,
                        title="Distribuição dos Valores Contratados",
                        color_discrete_sequence=['#667eea']
                    )
                    fig_hist.update_layout(height=400)
                    st.plotly_chart(fig_hist, use_container_width=True)
            
            # Tabela de faturamento formatada
            st.subheader("📋 Planilha de Faturamento Detalhada")
            
            # Formatar dados para exibição
            df_display_faturamento = df_faturamento_final.copy()
            
            # Formatar colunas monetárias
            for col in ['Valor Contratado', 'Penalidade', 'Desconto Alternativo', 'Valor Final']:
                if col in df_display_faturamento.columns:
                    df_display_faturamento[col] = df_display_faturamento[col].apply(
                        lambda x: f"R$ {x:,.2f}" if pd.notna(x) else "R$ 0,00"
                    )
            
            # Formatar colunas de porcentagem
            for col in ['Disponibilidade', 'SLA Disponibilidade']:
                if col in df_display_faturamento.columns:
                    df_display_faturamento[col] = df_display_faturamento[col].apply(
                        lambda x: f"{x:.2%}" if pd.notna(x) else "0,00%"
                    )
            
            st.dataframe(df_display_faturamento, use_container_width=True)
            
            # Botão para download da planilha de faturamento
            def criar_planilha_faturamento(df):
                output = BytesIO()
                writer = pd.ExcelWriter(output, engine='openpyxl')
                
                # Criar a planilha com formatação similar ao exemplo
                df_export = df_faturamento_final.copy()
                
                # Adicionar linhas de cabeçalho
                header_rows = pd.DataFrame({
                    'Circuito': ['', '', f'Planilha de faturamento referente aos serviços prestados em {mes_atual}', ''],
                    'Valor Contratado': ['', '', '', ''],
                    'Disponibilidade': ['', '', '', ''],
                    'SLA Disponibilidade': ['', '', '', ''],
                    'Penalidade': ['', '', '', ''],
                    'Desconto Alternativo': ['', '', '', ''],
                    'Valor Final': ['', '', '', '']
                })
                
                # Adicionar linhas de totais no final
                total_row = pd.DataFrame({
                    'Circuito': ['TOTAL'],
                    'Valor Contratado': [total_valor_contratado],
                    'Disponibilidade': [''],
                    'SLA Disponibilidade': [''],
                    'Penalidade': [total_penalidade],
                    'Desconto Alternativo': [total_desconto_alternativo],
                    'Valor Final': [total_valor_final]
                })
                
                # Combinar tudo
                df_final_export = pd.concat([header_rows, df_export, total_row], ignore_index=True)
                
                df_final_export.to_excel(writer, index=False, sheet_name='Faturamento_Pronto')
                writer.close()
                processed_data = output.getvalue()
                return processed_data
            
            excel_faturamento_data = criar_planilha_faturamento(df_faturamento_final)
            
            st.download_button(
                label="💾 Baixar Planilha de Faturamento Pronto",
                data=excel_faturamento_data,
                file_name=f"faturamento_pronto_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
        except Exception as e:
            st.error(f"❌ Erro ao processar planilha de faturamento: {e}")
            st.exception(e)
    
    else:
        st.info("⏳ Por favor, processe os dados na aba 'Validação SLA' primeiro para gerar a planilha de faturamento.")
        
        # Mostrar exemplo de como será a estrutura da planilha
        st.subheader("📝 Estrutura da Planilha de Faturamento")
        exemplo_df = pd.DataFrame({
            'Circuito': ['CIRCUITO001', 'CIRCUITO002', 'CIRCUITO003'],
            'Valor Contratado': ['R$ 10.000,00', 'R$ 15.000,00', 'R$ 8.000,00'],
            'Disponibilidade': ['98,25%', '97,50%', '99,10%'],
            'SLA Disponibilidade': ['99,00%', '99,00%', '99,00%'],
            'Penalidade': ['R$ -175,00', 'R$ -375,00', 'R$ 0,00'],
            'Desconto Alternativo': ['R$ 175,00', 'R$ 375,00', 'R$ 72,00'],
            'Valor Final': ['R$ 9.825,00', 'R$ 14.625,00', 'R$ 8.000,00']
        })
        st.dataframe(exemplo_df)
        st.info("💡 Esta será a estrutura da planilha de faturamento gerada com base nos dados processados.")