import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
from datetime import datetime

# ==============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA E ESTILO
# ==============================================================================
st.set_page_config(
    page_title="Dashboard de Qualidade",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Personalizado (KPIs Escuros e Letras Grandes)
st.markdown("""
<style>
    /* Estilo dos Cards de KPI (Modo Escuro) */
    div.kpi-card {
        background-color: #262730; 
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
        border: 1px solid #444;
        margin-bottom: 10px;
    }
    div.kpi-card h3 {
        color: #d3d3d3; /* Cinza claro para o título */
        font-size: 18px;
        margin: 0;
        font-weight: normal;
    }
    div.kpi-card h2 {
        color: #ffffff; /* Branco para o número */
        font-size: 36px; /* Aumentei a fonte */
        margin: 10px 0;
        font-weight: bold;
    }
    div.kpi-card span {
        font-size: 14px;
        color: #aaaaaa;
    }
    .block-container { padding-top: 2rem; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. CARREGAMENTO DE DADOS
# ==============================================================================
@st.cache_data(ttl=600)
def carregar_dados():
    arquivo = "NOTAS_QUALIDADE.xlsx"
    try:
        df = pd.read_excel(arquivo, sheet_name="BD")
        df['DATA FUSO BR'] = pd.to_datetime(df['DATA FUSO BR'])
        
        # Ordenação dos meses
        month_map = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho',
                     7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}
        if 'DATA FUSO BR' in df.columns:
            df['Mês_Nome'] = df['DATA FUSO BR'].dt.month.map(month_map)
            
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None

df = carregar_dados()

if df is None:
    st.stop()

# ==============================================================================
# 3. BARRA LATERAL E FILTROS
# ==============================================================================
with st.sidebar:
    # 1. LOGO (Certifique-se de fazer upload do arquivo 'logo.png' no GitHub)
    try:
        st.image("logo.png", use_container_width=True) 
    except:
        st.warning("Logo não encontrado. Faça upload de 'logo.png'.")
    
    page = option_menu(
        menu_title="Navegação",
        options=['Visão Geral', 'Report Detalhado'],
        icons=['speedometer2', 'table'],
        menu_icon='cast',
        default_index=0,
    )
    
    st.markdown("---")
    st.header("🎛️ Filtros")
    
    # Filtro de Data
    min_date = df['DATA FUSO BR'].min().date()
    max_date = df['DATA FUSO BR'].max().date()
    col_d1, col_d2 = st.columns(2)
    data_inicio = col_d1.date_input("Início", min_date, min_value=min_date, max_value=max_date)
    data_fim = col_d2.date_input("Fim", max_date, min_value=min_date, max_value=max_date)

    # Filtros Cascata
    lista_accounts = sorted(list(df['Account'].unique()))
    lista_accounts.insert(0, "TODOS")
    sel_account = st.selectbox("Account:", lista_accounts)
    
    df_step1 = df[df['Account'] == sel_account] if sel_account != "TODOS" else df
    
    lista_supervisores = sorted(list(df_step1['SUPERVISOR'].dropna().unique()))
    lista_supervisores.insert(0, "TODOS")
    sel_supervisor = st.selectbox("Supervisor:", lista_supervisores)
    
    df_step2 = df_step1[df_step1['SUPERVISOR'] == sel_supervisor] if sel_supervisor != "TODOS" else df_step1
    
    lista_hierarquia = sorted(list(df_step2['HIERARQUIA AVALIADOR'].dropna().unique()))
    lista_hierarquia.insert(0, "TODOS")
    sel_hierarquia = st.selectbox("Hierarquia:", lista_hierarquia)

    # 2. META FIXA (Removido do visual, fixado no código)
    meta_qualidade = 90

# ==============================================================================
# 4. FILTRAGEM
# ==============================================================================
mask_data = (df['DATA FUSO BR'].dt.date >= data_inicio) & (df['DATA FUSO BR'].dt.date <= data_fim)
df_filtrado = df.loc[mask_data]

if sel_account != "TODOS": df_filtrado = df_filtrado[df_filtrado["Account"] == sel_account]
if sel_supervisor != "TODOS": df_filtrado = df_filtrado[df_filtrado["SUPERVISOR"] == sel_supervisor]
if sel_hierarquia != "TODOS": df_filtrado = df_filtrado[df_filtrado["HIERARQUIA AVALIADOR"] == sel_hierarquia]

# Ordenação Meses
month_order = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
               'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
if 'Mês_Nome' in df_filtrado.columns:
    df_filtrado['Mês_Nome'] = pd.Categorical(df_filtrado['Mês_Nome'], categories=month_order, ordered=True)
    df_filtrado.sort_values('DATA FUSO BR', inplace=True)

# ==============================================================================
# 5. PÁGINA 1: VISÃO GERAL
# ==============================================================================
if page == "Visão Geral":
    st.title(f"📊 Dashboard de Performance")
    st.markdown(f"**Período:** {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}")
    st.markdown("---")

    total_avaliacoes = df_filtrado.shape[0]
    
    if total_avaliacoes > 0:
        media_score = df_filtrado["Internal Score With Bonus And Fatal Error (%)"].mean()
        delta_meta = media_score - meta_qualidade
        # Lógica de cor da borda do card
        cor_borda = "#2ca02c" if delta_meta >= 0 else "#d62728" # Verde ou Vermelho
        cor_texto_delta = "#2ca02c" if delta_meta >= 0 else "#d62728"
        
        perc_fb_aplicado = (df_filtrado["FEEDBACK APLICADO"].sum() / total_avaliacoes) * 100
        notas_100 = df_filtrado[df_filtrado['Internal Score With Bonus And Fatal Error (%)'] == 100].shape[0]
        notas_0 = df_filtrado[df_filtrado['Internal Score With Bonus And Fatal Error (%)'] == 0].shape[0]
    else:
        media_score, delta_meta, perc_fb_aplicado, notas_100, notas_0 = 0, 0, 0, 0, 0
        cor_borda = "#555"
        cor_texto_delta = "#999"

    # 3. CARDS DE KPI (FUNDO ESCURO, LETRA MAIOR)
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f"""<div class="kpi-card" style="border-left: 5px solid #0083B8;"><h3>Avaliações</h3><h2>{total_avaliacoes}</h2></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="kpi-card" style="border-left: 5px solid {cor_borda};">
            <h3>Nota Média</h3>
            <h2 style="color:{cor_texto_delta}">{media_score:.1f}%</h2>
            <span>Meta: {meta_qualidade}%</span>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="kpi-card" style="border-left: 5px solid #f0ad4e;"><h3>% Feedback</h3><h2>{perc_fb_aplicado:.1f}%</h2></div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""<div class="kpi-card" style="border-left: 5px solid #2ca02c;"><h3>Notas 100</h3><h2>{notas_100}</h2></div>""", unsafe_allow_html=True)
    with col5:
        st.markdown(f"""<div class="kpi-card" style="border-left: 5px solid #d62728;"><h3>Notas 0</h3><h2>{notas_0}</h2></div>""", unsafe_allow_html=True)

    st.markdown("---")

    # Gráficos
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        media_mes = df_filtrado.groupby('Mês_Nome', observed=True)['Internal Score With Bonus And Fatal Error (%)'].mean().reset_index()
        fig_evolucao = px.area(media_mes, x='Mês_Nome', y='Internal Score With Bonus And Fatal Error (%)', title="<b>Evolução Mensal</b>", markers=True)
        fig_evolucao.update_traces(line_color='#0083B8', fillcolor='rgba(0, 131, 184, 0.2)')
        fig_evolucao.add_hline(y=meta_qualidade, line_dash="dot", line_color="red")
        fig_evolucao.update_yaxes(range=[0, 110])
        st.plotly_chart(fig_evolucao, use_container_width=True)

    with col_g2:
        # 4. GRÁFICO AGORA É POR ACCOUNT
        media_acc = df_filtrado.groupby('Account')['Internal Score With Bonus And Fatal Error (%)'].mean().reset_index().sort_values('Internal Score With Bonus And Fatal Error (%)')
        fig_barras = px.bar(media_acc, y='Account', x='Internal Score With Bonus And Fatal Error (%)', title="<b>Média por Account</b>", text_auto='.1f', orientation='h')
        cores = ['#d3d3d3' if x < meta_qualidade else '#0083B8' for x in media_acc['Internal Score With Bonus And Fatal Error (%)']]
        fig_barras.update_traces(marker_color=cores)
        fig_barras.add_vline(x=meta_qualidade, line_dash="dot", line_color="red")
        st.plotly_chart(fig_barras, use_container_width=True)

    # Linha 2 de Gráficos
    col_g3, col_g4 = st.columns(2)
    with col_g3:
        # 5. CORREÇÃO DO ERRO DO DONUT (usando px.pie com hole)
        values = [df_filtrado["FEEDBACK APLICADO"].sum(), df_filtrado["FEEDBACK PENDENTE"].sum(), df_filtrado["FEEDBACK NÃO APLICADO"].sum()]
        fig_pizza = px.pie(values=values, names=['Aplicado', 'Pendente', 'Não Aplicado'], title="<b>Status Feedback</b>", 
                           color_discrete_sequence=['#2ca02c', '#ff7f0e', '#d62728'], hole=0.5)
        st.plotly_chart(fig_pizza, use_container_width=True)
        
    with col_g4:
        # Gráfico por Supervisor (movido para cá ou mantido se quiser ver detalhe)
        media_sup = df_filtrado.groupby('SUPERVISOR')['Internal Score With Bonus And Fatal Error (%)'].mean().reset_index().head(10)
        fig_sup = px.bar(media_sup, x='SUPERVISOR', y='Internal Score With Bonus And Fatal Error (%)', title="<b>Top Supervisores</b>", text_auto='.1f')
        st.plotly_chart(fig_sup, use_container_width=True)

# ==============================================================================
# 6. PÁGINA 2: REPORT DETALHADO (QUARTIS INCLUÍDOS)
# ==============================================================================
elif page == "Report Detalhado":
    st.title("📑 Relatório Detalhado")
    
    # 6. ANÁLISE DE QUARTIL (Recolocada aqui)
    st.subheader("📊 Análise de Quartil (Operadores)")
    
    # Agrupar média por operador
    media_por_operador = df_filtrado.groupby('Auditee')['Internal Score With Bonus And Fatal Error (%)'].mean().reset_index()
    media_por_operador.rename(columns={'Internal Score With Bonus And Fatal Error (%)': 'Nota Média'}, inplace=True)
    
    if len(media_por_operador) >= 4:
        # Definição dos Quartis
        q1_limit = media_por_operador['Nota Média'].quantile(0.25)
        q2_limit = media_por_operador['Nota Média'].quantile(0.50)
        q3_limit = media_por_operador['Nota Média'].quantile(0.75)
        
        def classificar_quartil(media):
            if media > q3_limit: return "Q1 (Top)"
            elif media > q2_limit: return "Q2"
            elif media > q1_limit: return "Q3"
            else: return "Q4 (Bottom)"
        
        media_por_operador['Quartil'] = media_por_operador['Nota Média'].apply(classificar_quartil)
        
        # Tabela resumo dos Quartis
        resumo_quartil = media_por_operador.groupby('Quartil').agg(
            Qtd_Operadores=('Auditee', 'count'),
            Nota_Media_Grupo=('Nota Média', 'mean')
        ).reset_index()
        
        col_q1, col_q2 = st.columns([1, 2])
        with col_q1:
            st.table(resumo_quartil.style.format({"Nota_Media_Grupo": "{:.1f}"}))
        with col_q2:
            st.info(f"""
            **Q1 (Top):** Notas acima de {q3_limit:.1f}
            **Q4 (Bottom):** Notas abaixo de {q1_limit:.1f}
            """)
            
        # Exibir lista completa com quartis
        with st.expander("Ver Classificação de Todos os Operadores"):
            st.dataframe(media_por_operador.sort_values('Nota Média', ascending=False), use_container_width=True)
    else:
        st.warning("Dados insuficientes para cálculo de Quartil (mínimo 4 operadores).")
    
    st.markdown("---")
    st.subheader("📥 Dados Gerais")
    
    cols_visualizacao = ['DATA FUSO BR', 'Auditee', 'SUPERVISOR', 'Internal Score With Bonus And Fatal Error (%)', 'FEEDBACK APLICADO', 'Account']
    cols_finais = [c for c in cols_visualizacao if c in df_filtrado.columns]
    
    st.dataframe(df_filtrado[cols_finais].sort_values('DATA FUSO BR', ascending=False), use_container_width=True, hide_index=True)
    
    @st.cache_data
    def convert_df(df): return df.to_csv(index=False).encode('utf-8')
    csv = convert_df(df_filtrado)
    st.download_button(label="📥 Baixar Excel (CSV)", data=csv, file_name=f'report_completo.csv', mime='text/csv')
    
    st.subheader("🚨 Top Ofensores (Nota 0)")
    top_ofensores = df_filtrado[df_filtrado['Internal Score With Bonus And Fatal Error (%)'] == 0].groupby(['Auditee', 'SUPERVISOR']).size().reset_index(name='Qtd Notas 0').sort_values('Qtd Notas 0', ascending=False).head(10)
    if not top_ofensores.empty: st.table(top_ofensores)
    else: st.success("Sem notas 0 no período.")

st.markdown("""<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;}</style>""", unsafe_allow_html=True)
