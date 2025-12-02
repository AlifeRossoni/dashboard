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

# CSS Personalizado (KPIs Alinhados e Centralizados)
st.markdown("""
<style>
    /* Cards KPI - Ajuste de Alinhamento */
    div.kpi-card {
        background-color: #262730; 
        border-radius: 12px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        border: 1px solid #444;
        margin-bottom: 15px;
        height: 150px; /* Altura fixa */
        display: flex;
        flex-direction: column;
        justify-content: center; /* Centraliza Verticalmente */
        align-items: center;     /* Centraliza Horizontalmente */
    }
    
    div.kpi-card h3 { 
        color: #d3d3d3; 
        font-size: 14px; 
        margin: 0 0 10px 0 !important; /* Força margem */
        text-transform: uppercase; 
        letter-spacing: 1px;
        line-height: 1.2;
    }
    
    div.kpi-card h2 { 
        color: #ffffff; 
        font-size: 32px; 
        margin: 0 !important; /* Remove margem padrão */
        font-weight: 700;
        line-height: 1;
    }
    
    div.kpi-card span { 
        font-size: 12px; 
        color: #aaaaaa; 
        margin-top: 8px; 
        display: block; 
    }
    
    /* Ajustes Gerais */
    .block-container { padding-top: 1rem; }
    section[data-testid="stSidebar"] { background-color: #1e1e1e; }
    .obs-text { font-size: 12px; color: #888; font-style: italic; }
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
        
        # Renomear coluna de Nota se necessário
        col_nota = "Internal Score With Bonus And Fatal Error (%)"
        if col_nota in df.columns:
            df.rename(columns={col_nota: "Nota"}, inplace=True)
        
        month_map = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho',
                     7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}
        if 'DATA FUSO BR' in df.columns:
            df['Mês_Nome'] = df['DATA FUSO BR'].dt.month.map(month_map)
            df['Dia_Semana'] = df['DATA FUSO BR'].dt.day_name()
            
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None

df = carregar_dados()

if df is None: st.stop()

# ==============================================================================
# 3. BARRA LATERAL
# ==============================================================================
with st.sidebar:
    try: st.image("logo.png", use_container_width=True) 
    except: pass 
    
    page = option_menu(
        menu_title=None,
        options=['Visão Geral', 'Report Detalhado'],
        icons=['graph-up-arrow', 'file-earmark-spreadsheet'],
        menu_icon='cast',
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#0083B8", "font-size": "18px"}, 
            "nav-link": {"font-size": "15px", "text-align": "left", "margin": "5px", "color": "#eee", "border-radius": "10px"},
            "nav-link-selected": {"background-color": "#0083B8", "color": "white"},
        }
    )
    
    st.markdown("---")
    st.markdown("<h3 style='text-align: left; color: #0083B8;'>🎛️ Filtros</h3>", unsafe_allow_html=True)
    
    min_date = df['DATA FUSO BR'].min().date()
    max_date = df['DATA FUSO BR'].max().date()
    col_d1, col_d2 = st.columns(2)
    data_inicio = col_d1.date_input("Início", min_date, min_value=min_date, max_value=max_date)
    data_fim = col_d2.date_input("Fim", max_date, min_value=min_date, max_value=max_date)

    # CASCATA
    lista_accounts = sorted(list(df['Account'].unique()))
    lista_accounts.insert(0, "TODOS")
    sel_account = st.selectbox("Account:", lista_accounts)
    df_s1 = df[df['Account'] == sel_account] if sel_account != "TODOS" else df
    
    if 'COORDENADOR' in df.columns:
        lista_coord = sorted(list(df_s1['COORDENADOR'].dropna().unique()))
        lista_coord.insert(0, "TODOS")
        sel_coordenador = st.selectbox("Coordenador:", lista_coord)
        df_s2 = df_s1[df_s1['COORDENADOR'] == sel_coordenador] if sel_coordenador != "TODOS" else df_s1
    else: sel_coordenador, df_s2 = "TODOS", df_s1

    lista_supervisores = sorted(list(df_s2['SUPERVISOR'].dropna().unique()))
    lista_supervisores.insert(0, "TODOS")
    sel_supervisor = st.selectbox("Supervisor:", lista_supervisores)
    df_s3 = df_s2[df_s2['SUPERVISOR'] == sel_supervisor] if sel_supervisor != "TODOS" else df_s2
    
    if 'CÉLULA' in df.columns:
        lista_celula = sorted(list(df_s3['CÉLULA'].dropna().unique()))
        lista_celula.insert(0, "TODOS")
        sel_celula = st.selectbox("Célula:", lista_celula)
        df_s4 = df_s3[df_s3['CÉLULA'] == sel_celula] if sel_celula != "TODOS" else df_s3
    else: sel_celula, df_s4 = "TODOS", df_s3

    if 'TIPO MONITORIA' in df.columns:
        lista_tipo = sorted(list(df_s4['TIPO MONITORIA'].dropna().unique()))
        lista_tipo.insert(0, "TODOS")
        sel_tipo_mon = st.selectbox("Tipo Monitoria:", lista_tipo)
    else: sel_tipo_mon = "TODOS"
    
    lista_hierarquia = sorted(list(df_s4['HIERARQUIA AVALIADOR'].dropna().unique()))
    lista_hierarquia.insert(0, "TODOS")
    sel_hierarquia = st.selectbox("Hierarquia:", lista_hierarquia)

# ==============================================================================
# 4. FILTRAGEM FINAL
# ==============================================================================
mask_data = (df['DATA FUSO BR'].dt.date >= data_inicio) & (df['DATA FUSO BR'].dt.date <= data_fim)
df_filtrado = df.loc[mask_data]

if sel_account != "TODOS": df_filtrado = df_filtrado[df_filtrado["Account"] == sel_account]
if sel_coordenador != "TODOS": df_filtrado = df_filtrado[df_filtrado["COORDENADOR"] == sel_coordenador]
if sel_supervisor != "TODOS": df_filtrado = df_filtrado[df_filtrado["SUPERVISOR"] == sel_supervisor]
if sel_celula != "TODOS": df_filtrado = df_filtrado[df_filtrado["CÉLULA"] == sel_celula]
if sel_tipo_mon != "TODOS": df_filtrado = df_filtrado[df_filtrado["TIPO MONITORIA"] == sel_tipo_mon]
if sel_hierarquia != "TODOS": df_filtrado = df_filtrado[df_filtrado["HIERARQUIA AVALIADOR"] == sel_hierarquia]

month_order = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
if 'Mês_Nome' in df_filtrado.columns:
    df_filtrado['Mês_Nome'] = pd.Categorical(df_filtrado['Mês_Nome'], categories=month_order, ordered=True)
    df_filtrado.sort_values('DATA FUSO BR', inplace=True)

# Meta
if "META" in df_filtrado.columns:
    meta_qualidade = df_filtrado["META"].mean() if sel_account == "TODOS" else df_filtrado["META"].max()
else: meta_qualidade = 90

# ==============================================================================
# 5. VISÃO GERAL
# ==============================================================================
if page == "Visão Geral":
    st.title(f"📊 Dashboard de Performance")
    st.markdown(f"**Período:** {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}")
    st.markdown("---")

    total_avaliacoes = df_filtrado.shape[0]
    
    if total_avaliacoes > 0:
        media_score = df_filtrado["Nota"].mean()
        delta_meta = media_score - meta_qualidade
        cor_borda = "#2ca02c" if delta_meta >= 0 else "#d62728"
        cor_texto_delta = "#2ca02c" if delta_meta >= 0 else "#d62728"
        
        perc_fb_aplicado = (df_filtrado["FEEDBACK APLICADO"].sum() / total_avaliacoes) * 100
        notas_100 = df_filtrado[df_filtrado['Nota'] == 100].shape[0]
        notas_0 = df_filtrado[df_filtrado['Nota'] == 0].shape[0]
    else:
        media_score, delta_meta, perc_fb_aplicado, notas_100, notas_0 = 0, 0, 0, 0, 0
        cor_borda = "#555"
        cor_texto_delta = "#999"

    # CARDS KPI (CSS Atualizado)
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: st.markdown(f"""<div class="kpi-card" style="border-left: 5px solid #0083B8;"><h3>Avaliações</h3><h2>{total_avaliacoes}</h2></div>""", unsafe_allow_html=True)
    with col2: st.markdown(f"""<div class="kpi-card" style="border-left: 5px solid {cor_borda};"><h3>Nota Média</h3><h2 style="color:{cor_texto_delta}">{media_score:.1f}%</h2><span>Meta: {meta_qualidade:.1f}%</span></div>""", unsafe_allow_html=True)
    with col3: st.markdown(f"""<div class="kpi-card" style="border-left: 5px solid #f0ad4e;"><h3>% Feedback</h3><h2>{perc_fb_aplicado:.1f}%</h2></div>""", unsafe_allow_html=True)
    with col4: st.markdown(f"""<div class="kpi-card" style="border-left: 5px solid #2ca02c;"><h3>Notas 100</h3><h2>{notas_100}</h2></div>""", unsafe_allow_html=True)
    with col5: st.markdown(f"""<div class="kpi-card" style="border-left: 5px solid #d62728;"><h3>Notas 0</h3><h2>{notas_0}</h2></div>""", unsafe_allow_html=True)

    st.markdown("---")

    # Linha 1
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        media_mes = df_filtrado.groupby('Mês_Nome', observed=True)['Nota'].mean().reset_index()
        fig_evolucao = px.area(media_mes, x='Mês_Nome', y='Nota', title="<b>Evolução Mensal (Média)</b>", markers=True)
        fig_evolucao.update_traces(line_color='#0083B8', fillcolor='rgba(0, 131, 184, 0.2)')
        fig_evolucao.add_hline(y=meta_qualidade, line_dash="dot", line_color="red")
        fig_evolucao.update_yaxes(range=[0, 110])
        st.plotly_chart(fig_evolucao, use_container_width=True)

    with col_g2:
        media_dia = df_filtrado.groupby(df_filtrado['DATA FUSO BR'].dt.date)['Nota'].mean().reset_index()
        fig_dia = px.line(media_dia, x='DATA FUSO BR', y='Nota', title="<b>Evolução Diária (Nota)</b>")
        fig_dia.update_traces(line_color='#f0ad4e')
        fig_dia.add_hline(y=meta_qualidade, line_dash="dot", line_color="red")
        st.plotly_chart(fig_dia, use_container_width=True)

    # Linha 2
    col_g3, col_g4 = st.columns(2)
    with col_g3:
        media_acc = df_filtrado.groupby('Account')['Nota'].mean().reset_index().sort_values('Nota')
        fig_barras = px.bar(media_acc, y='Account', x='Nota', title="<b>Média por Account</b>", text_auto='.1f', orientation='h')
        cores = ['#d3d3d3' if x < meta_qualidade else '#0083B8' for x in media_acc['Nota']]
        fig_barras.update_traces(marker_color=cores)
        fig_barras.add_vline(x=meta_qualidade, line_dash="dot", line_color="red")
        st.plotly_chart(fig_barras, use_container_width=True)
        
    with col_g4:
        # Pareto por CÉLULA e MÉDIA DA NOTA
        if 'CÉLULA' in df_filtrado.columns:
            pareto_data = df_filtrado.groupby('CÉLULA')['Nota'].mean().reset_index().sort_values('Nota', ascending=False)
            
            # Cálculo do Acumulado (baseado na soma das médias para o pareto visual)
            pareto_data['Acumulado'] = pareto_data['Nota'].cumsum() / pareto_data['Nota'].sum() * 100
            
            fig_pareto = go.Figure()
            fig_pareto.add_trace(go.Bar(x=pareto_data['CÉLULA'], y=pareto_data['Nota'], name='Nota Média', marker_color='#0083B8'))
            fig_pareto.add_trace(go.Scatter(x=pareto_data['CÉLULA'], y=pareto_data['Acumulado'], name='% Acumulado', yaxis='y2', mode='lines+markers', line_color='#d62728'))
            
            fig_pareto.update_layout(
                title="<b>Pareto: Célula por Média de Nota</b>",
                yaxis=dict(title="Nota Média"),
                yaxis2=dict(title="% Acumulado", overlaying='y', side='right', range=[0, 110]),
                showlegend=False
            )
            st.plotly_chart(fig_pareto, use_container_width=True)
        else:
            st.info("Coluna 'CÉLULA' não encontrada para gerar Pareto.")

    # Linha 3
    col_g5, col_g6 = st.columns(2)
    with col_g5:
        values = [df_filtrado["FEEDBACK APLICADO"].sum(), df_filtrado["FEEDBACK PENDENTE"].sum(), df_filtrado["FEEDBACK NÃO APLICADO"].sum()]
        fig_pizza = px.pie(values=values, names=['Aplicado', 'Pendente', 'Não Aplicado'], title="<b>Status Feedback</b>", 
                           color_discrete_sequence=['#2ca02c', '#ff7f0e', '#d62728'], hole=0.5)
        st.plotly_chart(fig_pizza, use_container_width=True)

    with col_g6:
        # Histograma (bargap adicionado para desgrudar)
        fig_hist = px.histogram(df_filtrado, x="Nota", nbins=20, title="<b>Distribuição de Notas</b>", color_discrete_sequence=['#0083B8'])
        fig_hist.update_layout(bargap=0.1) 
        st.plotly_chart(fig_hist, use_container_width=True)

# ==============================================================================
# 6. REPORT DETALHADO
# ==============================================================================
elif page == "Report Detalhado":
    st.title("📑 Relatório Detalhado")
    
    st.subheader("📊 Análise de Quartil")
    
    media_por_operador = df_filtrado.groupby('Auditee')['Nota'].mean().reset_index()
    media_por_operador.rename(columns={'Nota': 'Nota Média'}, inplace=True)
    
    if len(media_por_operador) >= 4:
        q1_limit = media_por_operador['Nota Média'].quantile(0.25)
        q2_limit = media_por_operador['Nota Média'].quantile(0.50)
        q3_limit = media_por_operador['Nota Média'].quantile(0.75)
        
        def classificar_quartil(media):
            if media > q3_limit: return "Q1 (Top)"
            elif media > q2_limit: return "Q2"
            elif media > q1_limit: return "Q3"
            else: return "Q4 (Bottom)"
        
        media_por_operador['Quartil'] = media_por_operador['Nota Média'].apply(classificar_quartil)
        
        # Agrupamento
        resumo_quartil = media_por_operador.groupby('Quartil').agg(
            Qtd_Operadores=('Auditee', 'count'),
            Nota_Media_Grupo=('Nota Média', 'mean'),
            Desvio_Padrao=('Nota Média', 'std')
        ).reset_index()
        
        # Cálculo de Dispersão (Média Q4 / Média Q1)
        try:
            # Filtra os valores para garantir que existem
            row_q1 = resumen_quartil[resumo_quartil['Quartil'] == "Q1 (Top)"]
            row_q4 = resumen_quartil[resumo_quartil['Quartil'] == "Q4 (Bottom)"]
            
            if not row_q1.empty and not row_q4.empty:
                nota_q1 = row_q1['Nota_Media_Grupo'].values[0]
                nota_q4 = row_q4['Nota_Media_Grupo'].values[0]
                # Q4 / Q1
                dispersao = (nota_q4 / nota_q1) if nota_q1 > 0 else 0
            else:
                dispersao = 0
        except:
            dispersao = 0
            
        col_q1, col_q2 = st.columns([1, 1.5])
        
        with col_q1:
            st.markdown("##### Resumo Estatístico")
            st.table(resumo_quartil.style.format({"Nota_Media_Grupo": "{:.1f}", "Desvio_Padrao": "{:.2f}"}))
            st.metric("Dispersão (Média Q4 / Média Q1)", f"{dispersao:.1%}")
            
        with col_q2:
            st.markdown("##### Nota Média por Quartil")
            fig_quartil = px.bar(resumo_quartil, x='Quartil', y='Nota_Media_Grupo', 
                                 text_auto='.1f', color='Quartil',
                                 title="Nota Média por Grupo",
                                 color_discrete_map={'Q1 (Top)': '#2ca02c', 'Q2': '#0083B8', 'Q3': '#f0ad4e', 'Q4 (Bottom)': '#d62728'})
            st.plotly_chart(fig_quartil, use_container_width=True)
        
        st.markdown(f"""
        <p class="obs-text">
        * Nota: Q1 (Top Performance) considera notas acima de {q3_limit:.1f}. 
        Q4 (Baixa Performance) considera notas abaixo de {q1_limit:.1f}.
        Dispersão calculada como (Média Q4 / Média Q1).
        </p>
        """, unsafe_allow_html=True)

        with st.expander("Ver Lista de Operadores por Quartil"):
            st.dataframe(media_por_operador.sort_values('Nota Média', ascending=False), use_container_width=True)
    else:
        st.warning("Dados insuficientes para cálculo de Quartil (mínimo 4 operadores).")
    
    st.markdown("---")
    
    st.subheader("📥 Dados Brutos")
    cols_visualizacao = ['DATA FUSO BR', 'Auditee', 'SUPERVISOR', 'COORDENADOR', 'CÉLULA', 'Nota', 'FEEDBACK APLICADO', 'Account']
    cols_finais = [c for c in cols_visualizacao if c in df_filtrado.columns]
    
    st.dataframe(df_filtrado[cols_finais].sort_values('DATA FUSO BR', ascending=False), use_container_width=True, hide_index=True)
    
    @st.cache_data
    def convert_df(df): return df.to_csv(index=False).encode('utf-8')
    csv = convert_df(df_filtrado)
    st.download_button(label="📥 Baixar Excel (CSV)", data=csv, file_name=f'report_completo.csv', mime='text/csv')
    
    st.markdown("---")
    
    st.subheader("🚨 Top Ofensores (Reincidentes em Nota 0)")
    try:
        reincidentes = df_filtrado[df_filtrado['Nota'] == 0]
        if not reincidentes.empty:
            top_ofensores = reincidentes.groupby(['Auditee', 'SUPERVISOR']).size().reset_index(name='Qtd Notas 0')
            top_ofensores = top_ofensores.sort_values('Qtd Notas 0', ascending=False).head(10)
            st.table(top_ofensores)
        else:
            st.success("Nenhuma nota 0 encontrada neste período.")
    except Exception as e:
        st.error(f"Erro ao calcular ofensores: {e}")

st.markdown("""<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;}</style>""", unsafe_allow_html=True)
