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
    page_title="Qualidade Concentrix",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Personalizado
st.markdown("""
<style>
    /* Estilo dos Cards de KPI */
    div.kpi-card {
        background-color: #262730; 
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        border: 1px solid #444;
        margin-bottom: 15px;
        transition: transform 0.2s;
    }
    div.kpi-card:hover {
        transform: scale(1.02);
    }
    div.kpi-card h3 {
        color: #d3d3d3;
        font-size: 16px;
        margin-bottom: 5px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    div.kpi-card h2 {
        color: #ffffff;
        font-size: 32px;
        margin: 0;
        font-weight: 700;
    }
    div.kpi-card span {
        font-size: 13px;
        color: #aaaaaa;
        margin-top: 5px;
        display: block;
    }
    .block-container { padding-top: 1rem; }
    
    section[data-testid="stSidebar"] {
        background-color: #1e1e1e;
    }
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
# 3. BARRA LATERAL (FILTROS E NAVEGAÇÃO)
# ==============================================================================
with st.sidebar:
    try:
        st.image("logo.png", use_container_width=True) 
    except:
        pass 
    
    page = option_menu(
        menu_title=None, 
        options=['Visão Geral', 'Report Detalhado'],
        icons=['graph-up-arrow', 'file-earmark-spreadsheet'],
        menu_icon='cast',
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#0083B8", "font-size": "18px"}, 
            "nav-link": {
                "font-size": "15px",
                "text-align": "left",
                "margin": "5px",
                "color": "#eee",
                "border-radius": "10px"
            },
            "nav-link-selected": {"background-color": "#0083B8", "color": "white"},
        }
    )
    
    st.markdown("---")
    st.markdown("<h3 style='text-align: left; color: #0083B8;'>🎛️ Filtros</h3>", unsafe_allow_html=True)
    
    # Filtro de Data
    min_date = df['DATA FUSO BR'].min().date()
    max_date = df['DATA FUSO BR'].max().date()
    col_d1, col_d2 = st.columns(2)
    data_inicio = col_d1.date_input("Início", min_date, min_value=min_date, max_value=max_date)
    data_fim = col_d2.date_input("Fim", max_date, min_value=min_date, max_value=max_date)

    # --- FILTROS EM CASCATA ---
    
    # 1. Account
    lista_accounts = sorted(list(df['Account'].unique()))
    lista_accounts.insert(0, "TODOS")
    sel_account = st.selectbox("Account:", lista_accounts)
    
    df_step1 = df[df['Account'] == sel_account] if sel_account != "TODOS" else df
    
    # 2. Coordenador
    if 'COORDENADOR' in df.columns:
        lista_coord = sorted(list(df_step1['COORDENADOR'].dropna().unique()))
        lista_coord.insert(0, "TODOS")
        sel_coordenador = st.selectbox("Coordenador:", lista_coord)
        df_step2 = df_step1[df_step1['COORDENADOR'] == sel_coordenador] if sel_coordenador != "TODOS" else df_step1
    else:
        sel_coordenador = "TODOS"
        df_step2 = df_step1

    # 3. Supervisor
    lista_supervisores = sorted(list(df_step2['SUPERVISOR'].dropna().unique()))
    lista_supervisores.insert(0, "TODOS")
    sel_supervisor = st.selectbox("Supervisor:", lista_supervisores)
    
    df_step3 = df_step2[df_step2['SUPERVISOR'] == sel_supervisor] if sel_supervisor != "TODOS" else df_step2
    
    # 4. Célula
    if 'CÉLULA' in df.columns:
        lista_celula = sorted(list(df_step3['CÉLULA'].dropna().unique()))
        lista_celula.insert(0, "TODOS")
        sel_celula = st.selectbox("Célula:", lista_celula)
        df_step4 = df_step3[df_step3['CÉLULA'] == sel_celula] if sel_celula != "TODOS" else df_step3
    else:
        sel_celula = "TODOS"
        df_step4 = df_step3

    # 5. Tipo de Monitoria
    if 'TIPO MONITORIA' in df.columns:
        lista_tipo = sorted(list(df_step4['TIPO MONITORIA'].dropna().unique()))
        lista_tipo.insert(0, "TODOS")
        sel_tipo_mon = st.selectbox("Tipo Monitoria:", lista_tipo)
    else:
        sel_tipo_mon = "TODOS"
    
    # 6. Hierarquia
    lista_hierarquia = sorted(list(df_step4['HIERARQUIA AVALIADOR'].dropna().unique()))
    lista_hierarquia.insert(0, "TODOS")
    sel_hierarquia = st.selectbox("Hierarquia:", lista_hierarquia)

# ==============================================================================
# 4. FILTRAGEM FINAL DO DATAFRAME
# ==============================================================================
mask_data = (df['DATA FUSO BR'].dt.date >= data_inicio) & (df['DATA FUSO BR'].dt.date <= data_fim)
df_filtrado = df.loc[mask_data]

if sel_account != "TODOS": df_filtrado = df_filtrado[df_filtrado["Account"] == sel_account]
if sel_coordenador != "TODOS": df_filtrado = df_filtrado[df_filtrado["COORDENADOR"] == sel_coordenador]
if sel_supervisor != "TODOS": df_filtrado = df_filtrado[df_filtrado["SUPERVISOR"] == sel_supervisor]
if sel_celula != "TODOS": df_filtrado = df_filtrado[df_filtrado["CÉLULA"] == sel_celula]
if sel_tipo_mon != "TODOS": df_filtrado = df_filtrado[df_filtrado["TIPO MONITORIA"] == sel_tipo_mon]
if sel_hierarquia != "TODOS": df_filtrado = df_filtrado[df_filtrado["HIERARQUIA AVALIADOR"] == sel_hierarquia]

# Ordenação Meses
month_order = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
               'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
if 'Mês_Nome' in df_filtrado.columns:
    df_filtrado['Mês_Nome'] = pd.Categorical(df_filtrado['Mês_Nome'], categories=month_order, ordered=True)
    df_filtrado.sort_values('DATA FUSO BR', inplace=True)

# Lógica da META Dinâmica
if "META" in df_filtrado.columns:
    if sel_account == "TODOS":
        meta_qualidade = df_filtrado["META"].mean()
    else:
        meta_qualidade = df_filtrado["META"].max()
else:
    meta_qualidade = 90 

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
        cor_borda = "#2ca02c" if delta_meta >= 0 else "#d62728"
        cor_texto_delta = "#2ca02c" if delta_meta >= 0 else "#d62728"
        
        perc_fb_aplicado = (df_filtrado["FEEDBACK APLICADO"].sum() / total_avaliacoes) * 100
        notas_100 = df_filtrado[df_filtrado['Internal Score With Bonus And Fatal Error (%)'] == 100].shape[0]
        notas_0 = df_filtrado[df_filtrado['Internal Score With Bonus And Fatal Error (%)'] == 0].shape[0]
    else:
        media_score, delta_meta, perc_fb_aplicado, notas_100, notas_0 = 0, 0, 0, 0, 0
        cor_borda = "#555"
        cor_texto_delta = "#999"

    # CARDS DE KPI
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f"""<div class="kpi-card" style="border-left: 5px solid #0083B8;"><h3>Avaliações</h3><h2>{total_avaliacoes}</h2></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="kpi-card" style="border-left: 5px solid {cor_borda};">
            <h3>Nota Média</h3>
            <h2 style="color:{cor_texto_delta}">{media_score:.1f}%</h2>
            <span>Meta: {meta_qualidade:.1f}%</span>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="kpi-card" style="border-left: 5px solid #f0ad4e;"><h3>% Feedback</h3><h2>{perc_fb_aplicado:.1f}%</h2></div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""<div class="kpi-card" style="border-left: 5px solid #2ca02c;"><h3>Notas 100</h3><h2>{notas_100}</h2></div>""", unsafe_allow_html=True)
    with col5:
        st.markdown(f"""<div class="kpi-card" style="border-left: 5px solid #d62728;"><h3>Notas 0</h3><h2>{notas_0}</h2></div>""", unsafe_allow_html=True)

    st.markdown("---")

    # Gráficos Linha 1
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        media_mes = df_filtrado.groupby('Mês_Nome', observed=True)['Internal Score With Bonus And Fatal Error (%)'].mean().reset_index()
        fig_evolucao = px.area(media_mes, x='Mês_Nome', y='Internal Score With Bonus And Fatal Error (%)', title="<b>Evolução Mensal</b>", markers=True)
        fig_evolucao.update_traces(line_color='#0083B8', fillcolor='rgba(0, 131, 184, 0.2)')
        fig_evolucao.add_hline(y=meta_qualidade, line_dash="dot", line_color="red")
        fig_evolucao.update_yaxes(range=[0, 110])
