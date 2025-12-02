import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
from datetime import datetime

# ==============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA E ESTILO CSS
# ==============================================================================
st.set_page_config(
    page_title="Dashboard de Qualidade Pro",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Personalizado para KPIs e Visual
st.markdown("""
<style>
    /* Estilo dos Cards de KPI */
    div.kpi-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        border-left: 5px solid #0083B8;
        margin-bottom: 10px;
    }
    div.kpi-card h3 {
        color: #555;
        font-size: 16px;
        margin: 0;
    }
    div.kpi-card h2 {
        color: #333;
        font-size: 28px;
        margin: 10px 0;
        font-weight: bold;
    }
    div.kpi-card span {
        font-size: 14px;
        color: #666;
    }
    
    /* Remover padding excessivo do topo */
    .block-container {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. CARREGAMENTO DE DADOS (CACHEADO)
# ==============================================================================
@st.cache_data(ttl=600)
def carregar_dados():
    # --------------------------------------------------------------------------
    # ATENÇÃO: SUBSTITUA PELO SEU LINK DO ONEDRIVE AQUI
    # --------------------------------------------------------------------------
    url_onedrive = "https://cnxmail-my.sharepoint.com/:x:/g/personal/alife_rossoni_concentrix_com/EVjkkrOOy0RChT0dvhbyligBUdamI013Nv52ZLL9U_HDKQ?e=eahaEN&download=1"
    
    try:
        df = pd.read_excel(url_onedrive, sheet_name="BD")
        # Converter colunas de data
        df['DATA FUSO BR'] = pd.to_datetime(df['DATA FUSO BR'])
        
        # Criar coluna de Mês Ordenável se não existir
        # (Opcional, caso queira garantir a ordem correta dos meses nos gráficos)
        month_map = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho',
                     7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}
        df['Mês_Nome'] = df['DATA FUSO BR'].dt.month.map(month_map)
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None

df = carregar_dados()

# Se der erro no carregamento, para o script
if df is None:
    st.stop()

# ==============================================================================
# 3. BARRA LATERAL (FILTROS EM CASCATA E NAVEGAÇÃO)
# ==============================================================================
with st.sidebar:
    # st.image("logo.png", use_container_width=True) # Descomente se tiver logo
    
    # --- Menu de Navegação ---
    page = option_menu(
        menu_title="Navegação",
        options=['Visão Geral', 'Report Detalhado'],
        icons=['speedometer2', 'table'],
        menu_icon='cast',
        default_index=0,
    )
    
    st.markdown("---")
    st.header("🎛️ Filtros Inteligentes")
    
    # 3.1 Filtro de Data (Periodo)
    min_date = df['DATA FUSO BR'].min().date()
    max_date = df['DATA FUSO BR'].max().date()
    
    col_d1, col_d2 = st.columns(2)
    data_inicio = col_d1.date_input("Início", min_date, min_value=min_date, max_value=max_date)
    data_fim = col_d2.date_input("Fim", max_date, min_value=min_date, max_value=max_date)

    # 3.2 Filtros em Cascata (Lógica: Um filtra o próximo)
    # Filtro 1: Account
    lista_accounts = sorted(list(df['Account'].unique()))
    lista_accounts.insert(0, "TODOS")
    sel_account = st.selectbox("Account:", lista_accounts)
    
    # Filtra DF temporário para alimentar o próximo filtro
    df_step1 = df[df['Account'] == sel_account] if sel_account != "TODOS" else df
    
    # Filtro 2: Supervisor (Baseado no Account selecionado)
    lista_supervisores = sorted(list(df_step1['SUPERVISOR'].dropna().unique()))
    lista_supervisores.insert(0, "TODOS")
    sel_supervisor = st.selectbox("Supervisor:", lista_supervisores)
    
    # Filtra DF temporário passo 2
    df_step2 = df_step1[df_step1['SUPERVISOR'] == sel_supervisor] if sel_supervisor != "TODOS" else df_step1
    
    # Filtro 3: Hierarquia
    lista_hierarquia = sorted(list(df_step2['HIERARQUIA AVALIADOR'].dropna().unique()))
    lista_hierarquia.insert(0, "TODOS")
    sel_hierarquia = st.selectbox("Hierarquia:", lista_hierarquia)

    # 3.3 Definição de Meta
    st.markdown("---")
    meta_qualidade = st.slider("🎯 Meta de Qualidade (%)", 0, 100, 90)

# ==============================================================================
# 4. APLICAÇÃO DOS FILTROS NO DATAFRAME PRINCIPAL
# ==============================================================================
# Filtro de Data
mask_data = (df['DATA FUSO BR'].dt.date >= data_inicio) & (df['DATA FUSO BR'].dt.date <= data_fim)
df_filtrado = df.loc[mask_data]

# Filtros Categóricos
if sel_account != "TODOS":
    df_filtrado = df_filtrado[df_filtrado["Account"] == sel_account]
if sel_supervisor != "TODOS":
    df_filtrado = df_filtrado[df_filtrado["SUPERVISOR"] == sel_supervisor]
if sel_hierarquia != "TODOS":
    df_filtrado = df_filtrado[df_filtrado["HIERARQUIA AVALIADOR"] == sel_hierarquia]

# Ordenação para gráficos de tempo
month_order = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
               'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
if 'Mês_Nome' in df_filtrado.columns:
    df_filtrado['Mês_Nome'] = pd.Categorical(df_filtrado['Mês_Nome'], categories=month_order, ordered=True)
    df_filtrado.sort_values('DATA FUSO BR', inplace=True)

# ==============================================================================
# 5. PÁGINA 1: VISÃO GERAL
# ==============================================================================
if page == "Visão Geral":
    st.title(f"📊 Dashboard de Performance - {sel_account}")
    st.markdown(f"**Período:** {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}")
    st.markdown("---")

    # 5.1 CÁLCULO DOS KPIs
    total_avaliacoes = df_filtrado.shape[0]
    
    if total_avaliacoes > 0:
        media_score = df_filtrado["Internal Score With Bonus And Fatal Error (%)"].mean()
        
        # Comparativo com a Meta
        delta_meta = media_score - meta_qualidade
        cor_delta = "green" if delta_meta >= 0 else "red"
        
        fb_aplicado = df_filtrado["FEEDBACK APLICADO"].sum()
        perc_fb_aplicado = (fb_aplicado / total_avaliacoes) * 100
        
        notas_100 = df_filtrado[df_filtrado['Internal Score With Bonus And Fatal Error (%)'] == 100].shape[0]
        notas_0 = df_filtrado[df_filtrado['Internal Score With Bonus And Fatal Error (%)'] == 0].shape[0]
    else:
        media_score, delta_meta, perc_fb_aplicado, notas_100, notas_0 = 0, 0, 0, 0, 0
        cor_delta = "gray"

    # 5.2 EXIBIÇÃO DOS CARDS (HTML/CSS)
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <h3>Total Avaliações</h3>
            <h2>{total_avaliacoes}</h2>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div class="kpi-card" style="border-left: 5px solid {cor_delta};">
            <h3>Nota Média</h3>
            <h2 style="color:{cor_delta}">{media_score:.1f}%</h2>
            <span>Meta: {meta_qualidade}%</span>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="kpi-card">
            <h3>% Feedback</h3>
            <h2>{perc_fb_aplicado:.1f}%</h2>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="kpi-card" style="border-left: 5px solid green;">
            <h3>Notas 100</h3>
            <h2>{notas_100}</h2>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        st.markdown(f"""
        <div class="kpi-card" style="border-left: 5px solid red;">
            <h3>Notas 0</h3>
            <h2>{notas_0}</h2>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 5.3 GRÁFICOS
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        # Gráfico de Evolução por Mês com Meta
        media_mes = df_filtrado.groupby('Mês_Nome', observed=True)['Internal Score With Bonus And Fatal Error (%)'].mean().reset_index()
        
        fig_evolucao = px.area(media_mes, x='Mês_Nome', y='Internal Score With Bonus And Fatal Error (%)',
                               title="<b>Evolução da Qualidade (Mês)</b>", markers=True)
        fig_evolucao.update_traces(line_color='#0083B8', fillcolor='rgba(0, 131, 184, 0.2)')
        
        # Adicionar Linha de Meta
        fig_evolucao.add_hline(y=meta_qualidade, line_dash="dot", line_color="red", 
                               annotation_text=f"Meta {meta_qualidade}%", annotation_position="top left")
        
        fig_evolucao.update_yaxes(range=[0, 110]) # Fixar escala
        st.plotly_chart(fig_evolucao, use_container_width=True)

    with col_g2:
        # Gráfico de Barras por Supervisor (Top 10 ou todos)
        media_sup = df_filtrado.groupby('SUPERVISOR')['Internal Score With Bonus And Fatal Error (%)'].mean().reset_index()
        media_sup = media_sup.sort_values('Internal Score With Bonus And Fatal Error (%)', ascending=True) # Ordenar
        
        fig_barras = px.bar(media_sup, y='SUPERVISOR', x='Internal Score With Bonus And Fatal Error (%)',
                            title="<b>Média por Supervisor</b>", text_auto='.1f', orientation='h')
        
        # Colora as barras dependendo da meta
        cores = ['#d3d3d3' if x < meta_qualidade else '#0083B8' for x in media_sup['Internal Score With Bonus And Fatal Error (%)']]
        fig_barras.update_traces(marker_color=cores)
        
        fig_barras.add_vline(x=meta_qualidade, line_dash="dot", line_color="red")
        st.plotly_chart(fig_barras, use_container_width=True)

    # Gráfico de Rosca Feedback
    col_g3, col_g4 = st.columns(2)
    with col_g3:
        labels = ['Aplicado', 'Pendente', 'Não Aplicado']
        values = [
            df_filtrado["FEEDBACK APLICADO"].sum(),
            df_filtrado["FEEDBACK PENDENTE"].sum(),
            df_filtrado["FEEDBACK NÃO APLICADO"].sum()
        ]
        fig_pizza = px.donut(values=values, names=labels, title="<b>Status de Feedback</b>",
                             color_discrete_sequence=['#2ca02c', '#ff7f0e', '#d62728'])
        st.plotly_chart(fig_pizza, use_container_width=True)
        
    with col_g4:
         # Notas por Account (Comparativo)
        if sel_account == "TODOS":
             media_acc = df_filtrado.groupby('Account')['Internal Score With Bonus And Fatal Error (%)'].mean().reset_index()
             fig_acc = px.bar(media_acc, x='Account', y='Internal Score With Bonus And Fatal Error (%)',
                              title="<b>Comparativo por Account</b>", text_auto='.1f',
                              color='Internal Score With Bonus And Fatal Error (%)', color_continuous_scale='Blues')
             st.plotly_chart(fig_acc, use_container_width=True)
        else:
            st.info("Selecione 'TODOS' no filtro de Account para ver o comparativo entre contas.")


# ==============================================================================
# 6. PÁGINA 2: REPORT DETALHADO (TABELAS E DOWNLOAD)
# ==============================================================================
elif page == "Report Detalhado":
    st.title("📑 Relatório Detalhado")
    st.markdown("Visualize os dados brutos e baixe o relatório.")
    
    # Exibir Tabela Interativa
    # Selecionar apenas colunas mais relevantes para visualização
    cols_visualizacao = ['DATA FUSO BR', 'Auditee', 'SUPERVISOR', 'Internal Score With Bonus And Fatal Error (%)', 
                         'FEEDBACK APLICADO', 'Account', 'CÉLULA']
    
    # Verifica se as colunas existem antes de mostrar
    cols_finais = [c for c in cols_visualizacao if c in df_filtrado.columns]
    
    st.dataframe(df_filtrado[cols_finais].sort_values('DATA FUSO BR', ascending=False), use_container_width=True, hide_index=True)
    
    st.markdown("### 📥 Exportar Dados")
    
    # Botão de Download
    @st.cache_data
    def convert_df(df):
        # Cache da conversão para CSV para não travar em arquivos grandes
        return df.to_csv(index=False).encode('utf-8')

    csv = convert_df(df_filtrado)

    st.download_button(
        label="Baixar Dados Filtrados (CSV)",
        data=csv,
        file_name=f'relatorio_qualidade_{datetime.now().strftime("%Y%m%d")}.csv',
        mime='text/csv',
    )
    
    st.markdown("---")
    st.subheader("Top Ofensores (Reincidentes em Nota 0)")
    
    reincidentes = df_filtrado[df_filtrado['Internal Score With Bonus And Fatal Error (%)'] == 0]
    top_ofensores = reincidentes.groupby(['Auditee', 'SUPERVISOR']).size().reset_index(name='Qtd Notas 0')
    top_ofensores = top_ofensores.sort_values('Qtd Notas 0', ascending=False).head(10)
    
    if not top_ofensores.empty:
        st.table(top_ofensores)
    else:
        st.success("Parabéns! Nenhuma nota 0 encontrada no período selecionado.")

# ==============================================================================
# 7. RODAPÉ
# ==============================================================================
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)