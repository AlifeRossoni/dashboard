import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu

# -- Configuração da Página --
st.set_page_config(page_title="Dashboard de Qualidade",
                   page_icon=":bar_chart:",
                   layout="wide")

# -- Carregamento dos Dados --
@st.cache_data
def carregar_dados():
    nome_do_arquivo = "NOTAS_QUALIDADE.xlsx"
    try:
        df = pd.read_excel(nome_do_arquivo, sheet_name="BD")
        df['DATA FUSO BR'] = pd.to_datetime(df['DATA FUSO BR'])
        return df
    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar o ficheiro '{nome_do_arquivo}': {e}. Verifique o nome do ficheiro e da planilha 'BD'.")
        return None

df = carregar_dados()

if df is not None:
    # -- NAVEGAÇÃO COM IMAGEM NO TOPO --
    with st.sidebar:
        # st.image("logo.png", use_container_width=True) # Descomente e adicione o seu logo aqui
        
        page = option_menu(
            menu_title=None,
            options=['Dashboard Principal', 'Report Qualidade'],
            icons=['house-door-fill', 'clipboard2-data-fill'],
            menu_icon='list-task',
            default_index=0,
            styles={
                "container": {"padding": "5!important", "background-color": "#262730"},
                "icon": {"color": "#ffffff", "font-size": "23px"}, 
                "nav-link": {
                    "font-size": "16px",
                    "text-align": "left",
                    "margin":"0px",
                    "color": "#ffffff",
                    "--hover-color": "#444444"
                },
                "nav-link-selected": {"background-color": "#0083B8"},
            }
        )

    # -- FILTROS --
    st.sidebar.header("Painel de Filtros")

    def get_options(column_name):
        options = list(df[column_name].dropna().unique())
        options.sort()
        options.insert(0, "TODOS")
        return options

    mes = st.sidebar.selectbox("Selecione o Mês:", options=get_options("MÊS"))
    account = st.sidebar.selectbox("Selecione o Account:", options=get_options("Account"))
    celula = st.sidebar.selectbox("Selecione a Célula:", options=get_options("CÉLULA"))
    semana = st.sidebar.selectbox("Selecione a Semana:", options=get_options("SEMANA"))
    hierarquia = st.sidebar.selectbox("Hierarquia do Avaliador:", options=get_options("HIERARQUIA AVALIADOR"))
    tipo_monitoria = st.sidebar.selectbox("Tipo de Monitoria:", options=get_options("TIPO MONITORIA"))
    supervisor = st.sidebar.selectbox("Selecione o Supervisor:", options=get_options("SUPERVISOR"))
    coordenador = st.sidebar.selectbox("Selecione o Coordenador:", options=get_options("COORDENADOR"))

    # -- Lógica de filtragem --
    df_filtrado = df.copy()
    if mes != "TODOS": df_filtrado = df_filtrado[df_filtrado["MÊS"] == mes]
    if account != "TODOS": df_filtrado = df_filtrado[df_filtrado["Account"] == account]
    if celula != "TODOS": df_filtrado = df_filtrado[df_filtrado["CÉLULA"] == celula]
    if semana != "TODOS": df_filtrado = df_filtrado[df_filtrado["SEMANA"] == semana]
    if hierarquia != "TODOS": df_filtrado = df_filtrado[df_filtrado["HIERARQUIA AVALIADOR"] == hierarquia]
    if tipo_monitoria != "TODOS": df_filtrado = df_filtrado[df_filtrado["TIPO MONITORIA"] == tipo_monitoria]
    if supervisor != "TODOS": df_filtrado = df_filtrado[df_filtrado["SUPERVISOR"] == supervisor]
    if coordenador != "TODOS": df_filtrado = df_filtrado[df_filtrado["COORDENADOR"] == coordenador]

    # Ordenação cronológica dos meses
    month_order = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                   'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    if 'MÊS' in df_filtrado.columns:
        df_filtrado['MÊS'] = pd.Categorical(df_filtrado['MÊS'], categories=month_order, ordered=True)

    # ---- PÁGINA 1: DASHBOARD PRINCIPAL ----
    if page == "Dashboard Principal":
        st.title(":bar_chart: Dashboard de Notas de Qualidade")
        st.markdown("##")

        total_avaliacoes = df_filtrado.shape[0]
        if total_avaliacoes > 0:
            media_interna = df_filtrado["Internal Score With Bonus And Fatal Error (%)"].mean()
            avaliacoes_operacao = df_filtrado[df_filtrado["HIERARQUIA AVALIADOR"] == "Operação"].shape[0]
            avaliacoes_qualidade = df_filtrado[df_filtrado["HIERARQUIA AVALIADOR"] == "Qualidade"].shape[0]
            soma_feedback_aplicado = df_filtrado["FEEDBACK APLICADO"].sum()
            soma_feedback_pendente = df_filtrado["FEEDBACK PENDENTE"].sum()
            percent_feedback_aplicado = (soma_feedback_aplicado / total_avaliacoes) * 100
            percent_feedback_pendente = (soma_feedback_pendente / total_avaliacoes) * 100
        else:
            media_interna, avaliacoes_operacao, avaliacoes_qualidade, percent_feedback_aplicado, percent_feedback_pendente, soma_feedback_pendente = 0, 0, 0, 0, 0, 0
        
        col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
        with col1: st.metric(label="**Qtd. Avaliações**", value=f"{total_avaliacoes}")
        with col2: st.metric(label="**Nota Qualidade Média**", value=f"{media_interna:.1f}")
        with col3: st.metric(label="**Aval. (Operação)**", value=f"{avaliacoes_operacao}")
        with col4: st.metric(label="**Aval. (Qualidade)**", value=f"{avaliacoes_qualidade}")
        with col5: st.metric(label="**% FB Aplicado**", value=f"{percent_feedback_aplicado:.1f}%")
        with col6: st.metric(label="**% FB Pendente**", value=f"{percent_feedback_pendente:.1f}%")
        with col7: st.metric(label="**Qtd. FB Pendente**", value=f"{soma_feedback_pendente}")
        
        st.markdown("---")
        
        if not df_filtrado.empty:
            st.subheader("Análises de Performance")
            col_a, col_b = st.columns(2)
            with col_a:
                media_por_mes = df_filtrado.groupby('MÊS', observed=True)['Internal Score With Bonus And Fatal Error (%)'].mean().reset_index()
                fig_media_mes = px.area(
                    media_por_mes, 
                    x='MÊS', 
                    y='Internal Score With Bonus And Fatal Error (%)', 
                    title='<b>Nota Qualidade por Mês</b>',
                    markers=True,
                    labels={'Internal Score With Bonus And Fatal Error (%)': 'Nota'}
                )
                fig_media_mes.update_traces(line_color='#0083B8', fillcolor='rgba(0, 131, 184, 0.2)')
                fig_media_mes.update_layout(yaxis_title="Nota Qualidade Média")
                st.plotly_chart(fig_media_mes, use_container_width=True)
                
                media_por_dia = df_filtrado.groupby(df_filtrado['DATA FUSO BR'].dt.date)['Internal Score With Bonus And Fatal Error (%)'].mean().reset_index()
                fig_media_dia = px.line(
                    media_por_dia, 
                    x='DATA FUSO BR', 
                    y='Internal Score With Bonus And Fatal Error (%)', 
                    title='<b>Nota Qualidade por Dia</b>', 
                    line_shape='spline',
                    labels={'Internal Score With Bonus And Fatal Error (%)': 'Nota'}
                )
                fig_media_dia.update_traces(mode='lines+markers')
                fig_media_dia.update_layout(yaxis_title="Nota Qualidade Média", xaxis_title="Data")
                st.plotly_chart(fig_media_dia, use_container_width=True)
            with col_b:
                media_segmento_mes = df_filtrado.groupby(['MÊS', 'Account'], observed=True)['Internal Score With Bonus And Fatal Error (%)'].mean().reset_index()
                fig_media_segmento_mes = px.bar(
                    media_segmento_mes, 
                    x='MÊS', 
                    y='Internal Score With Bonus And Fatal Error (%)', 
                    color='Account', 
                    barmode='group', 
                    title='<b>Nota Qualidade por Segmento e Mês</b>', 
                    text_auto='.1f',
                    labels={'Internal Score With Bonus And Fatal Error (%)': 'Nota'}
                )
                fig_media_segmento_mes.update_layout(yaxis_title="Nota Qualidade Média")
                st.plotly_chart(fig_media_segmento_mes, use_container_width=True)
                
                valores_feedback = [percent_feedback_aplicado, 100 - percent_feedback_aplicado]
                nomes_feedback = ['Aplicado', 'Não Aplicado']
                fig_rosca_feedback = go.Figure(data=[go.Pie(labels=nomes_feedback, values=valores_feedback, hole=.5)])
                fig_rosca_feedback.update_layout(title_text='<b>% de Feedback Aplicado</b>', annotations=[dict(text=f'{percent_feedback_aplicado:.1f}%', x=0.5, y=0.5, font_size=20, showarrow=False)])
                st.plotly_chart(fig_rosca_feedback, use_container_width=True)
            
            st.markdown("---")
            st.subheader("Análises de Conformidade e Oportunidades")
            col_c, col_d = st.columns(2)
            with col_c:
                feedback_segmento_mes = df_filtrado.groupby(['MÊS', 'Account'], observed=True)['FEEDBACK APLICADO'].apply(lambda x: (x.sum() / len(x)) * 100).reset_index(name='% Feedback Aplicado')
                fig_feedback_segmento_mes = px.bar(feedback_segmento_mes, x='MÊS', y='% Feedback Aplicado', color='Account', barmode='group', title='<b>% de Feedback por Segmento e Mês</b>')
                fig_feedback_segmento_mes.update_traces(texttemplate='%{y:.1f}%')
                st.plotly_chart(fig_feedback_segmento_mes, use_container_width=True)
                
                perc_nota_100 = (df_filtrado['NOTA 100'].sum() / total_avaliacoes) * 100
                fig_rosca_100 = go.Figure(data=[go.Pie(labels=['Nota 100', 'Outras Notas'], values=[perc_nota_100, 100 - perc_nota_100], hole=.5)])
                fig_rosca_100.update_layout(title_text='<b>% de Notas 100</b>', annotations=[dict(text=f'{perc_nota_100:.1f}%', x=0.5, y=0.5, font_size=20, showarrow=False)])
                st.plotly_chart(fig_rosca_100, use_container_width=True)
            with col_d:
                media_tempo_casa = df_filtrado.groupby('SITUAÇÃO DE CASA')['Internal Score With Bonus And Fatal Error (%)'].mean().reset_index()
                fig_media_tempo_casa = px.bar(
                    media_tempo_casa, 
                    x='SITUAÇÃO DE CASA', 
                    y='Internal Score With Bonus And Fatal Error (%)', 
                    title='<b>Nota Qualidade por Tempo de Casa</b>', 
                    text_auto='.1f',
                    labels={'Internal Score With Bonus And Fatal Error (%)': 'Nota'}
                )
                fig_media_tempo_casa.update_layout(yaxis_title="Nota Qualidade Média")
                st.plotly_chart(fig_media_tempo_casa, use_container_width=True)
                
                perc_nota_0 = (df_filtrado['NOTA 0'].sum() / total_avaliacoes) * 100
                fig_rosca_0 = go.Figure(data=[go.Pie(labels=['Nota 0', 'Outras Notas'], values=[perc_nota_0, 100 - perc_nota_0], hole=.5)])
                fig_rosca_0.update_layout(title_text='<b>% de Notas 0</b>', annotations=[dict(text=f'{perc_nota_0:.1f}%', x=0.5, y=0.5, font_size=20, showarrow=False)])
                st.plotly_chart(fig_rosca_0, use_container_width=True)
        else:
            st.warning("Nenhum dado encontrado para os filtros selecionados.")

    # ---- PÁGINA 2: REPORT QUALIDADE ----
    elif page == "Report Qualidade":
        st.title(":clipboard: Report Qualidade")
        st.markdown("---")

        if not df_filtrado.empty:
            st.subheader("Notas QA")
            col1, col2 = st.columns(2)
            with col1:
                media_por_mes = df_filtrado.groupby('MÊS', observed=True)['Internal Score With Bonus And Fatal Error (%)'].mean().reset_index()
                fig_media_mes = px.area(
                    media_por_mes, 
                    x='MÊS', 
                    y='Internal Score With Bonus And Fatal Error (%)', 
                    title='<b>Nota Qualidade por Mês</b>',
                    markers=True,
                    labels={'Internal Score With Bonus And Fatal Error (%)': 'Nota'}
                )
                fig_media_mes.update_traces(line_color='#0083B8', fillcolor='rgba(0, 131, 184, 0.2)')
                fig_media_mes.update_layout(yaxis_title="Nota Qualidade Média")
                st.plotly_chart(fig_media_mes, use_container_width=True)
            with col2:
                media_segmento_mes = df_filtrado.groupby(['MÊS', 'Account'], observed=True)['Internal Score With Bonus And Fatal Error (%)'].mean().reset_index()
                fig_media_segmento_mes = px.bar(
                    media_segmento_mes, 
                    x='MÊS', 
                    y='Internal Score With Bonus And Fatal Error (%)', 
                    color='Account', 
                    barmode='group', 
                    title='<b>Nota Qualidade por Segmento e Mês</b>', 
                    text_auto='.1f',
                    labels={'Internal Score With Bonus And Fatal Error (%)': 'Nota'}
                )
                fig_media_segmento_mes.update_layout(yaxis_title="Nota Qualidade Média")
                st.plotly_chart(fig_media_segmento_mes, use_container_width=True)

            st.markdown("---")
            st.subheader("Análise de Feedback por Supervisor")
            feedback_supervisor = df_filtrado.groupby('SUPERVISOR').agg(
                quantidade=('Auditee', 'count'),
                nota_qualidade_media=('Internal Score With Bonus And Fatal Error (%)', 'mean'),
                qnt_feedback_aplicado=('FEEDBACK APLICADO', 'sum'),
                qnt_feedback_nao_aplicado=('FEEDBACK NÃO APLICADO', 'sum'),
                qnt_feedback_pendente=('FEEDBACK PENDENTE', 'sum')
            ).reset_index()
            feedback_supervisor['%_feedback_aplicado'] = (feedback_supervisor['qnt_feedback_aplicado'] / feedback_supervisor['quantidade']) * 100
            feedback_supervisor['%_feedback_nao_aplicado'] = (feedback_supervisor['qnt_feedback_nao_aplicado'] / feedback_supervisor['quantidade']) * 100
            
            st.dataframe(feedback_supervisor.style.format({
                "nota_qualidade_media": "{:.1f}",
                "%_feedback_aplicado": "{:.1f}%",
                "%_feedback_nao_aplicado": "{:.1f}%"
            }), use_container_width=True)

            st.markdown("---")
            st.subheader("Top 10 Reincidentes em Nota 0")
            reincidentes_nota_0 = df_filtrado[df_filtrado['NOTA 0'] == 1]
            top_10 = reincidentes_nota_0.groupby(['Auditee', 'SUPERVISOR']).size().reset_index(name='Qtd. Notas 0')
            top_10 = top_10[top_10['Qtd. Notas 0'] >= 2].sort_values(by='Qtd. Notas 0', ascending=False).head(10)
            top_10 = top_10.rename(columns={'Auditee': 'Nome do Avaliado'})
            if not top_10.empty:
                st.dataframe(top_10, use_container_width=True)
            else:
                st.info("Nenhum reincidente (com 2 ou mais notas 0) encontrado.")

            st.markdown("---")
            st.subheader("Análise de Notas por Quartil")
            media_por_operador = df_filtrado.groupby('Auditee')['Internal Score With Bonus And Fatal Error (%)'].mean().reset_index()
            
            if len(media_por_operador) >= 4:
                media_por_operador = media_por_operador.rename(columns={'Internal Score With Bonus And Fatal Error (%)': 'nota_qualidade_media'})
                q1_limit = media_por_operador['nota_qualidade_media'].quantile(0.25)
                q2_limit = media_por_operador['nota_qualidade_media'].quantile(0.50)
                q3_limit = media_por_operador['nota_qualidade_media'].quantile(0.75)
                
                def classificar_quartil(media):
                    if media > q3_limit: return "Q1"
                    elif media > q2_limit: return "Q2"
                    elif media > q1_limit: return "Q3"
                    else: return "Q4"
                
                media_por_operador['Quartil'] = media_por_operador['nota_qualidade_media'].apply(classificar_quartil)
                df_com_quartil = pd.merge(df_filtrado, media_por_operador[['Auditee', 'Quartil']], on='Auditee', how='left')
                
                resumo_quartil = media_por_operador.groupby('Quartil').agg(
                    qnt_de_operadores=('Auditee', 'count'),
                    media_do_quartil=('nota_qualidade_media', 'mean')
                ).reset_index()
                
                qnt_avaliacoes_quartil = df_com_quartil.groupby('Quartil')['Auditee'].count().reset_index().rename(columns={'Auditee': 'qnt_de_avaliacoes'})
                resumo_quartil = pd.merge(resumo_quartil, qnt_avaliacoes_quartil, on='Quartil', how='left')
                
                total_operadores = resumo_quartil['qnt_de_operadores'].sum()
                resumo_quartil['representatividade_%'] = (resumo_quartil['qnt_de_operadores'] / total_operadores) * 100
                
                q1_data = resumo_quartil[resumo_quartil['Quartil'] == 'Q1']
                q4_data = resumo_quartil[resumo_quartil['Quartil'] == 'Q4']
                
                dispersao_nota = q4_data['media_do_quartil'].iloc[0] / q1_data['media_do_quartil'].iloc[0] if not q1_data.empty and not q4_data.empty and q1_data['media_do_quartil'].iloc[0] != 0 else 0
                amplitude = q1_data['qnt_de_avaliacoes'].iloc[0] - q4_data['qnt_de_avaliacoes'].iloc[0] if not q1_data.empty and not q4_data.empty else 0

                st.dataframe(resumo_quartil.style.format({
                    "media_do_quartil": "{:.1f}",
                    "representatividade_%": "{:.1f}%"
                }), use_container_width=True)
                
                col_disp, col_amp = st.columns(2)
                with col_disp:
                    st.metric("Dispersão (Média Q4 / Média Q1)", f"{dispersao_nota:.1%}")
                with col_amp:
                    st.metric("Amplitude (Avaliações Q1 - Q4)", f"{amplitude}")
            else:
                st.info("Não há operadores suficientes para uma análise de quartil.")
        else:
            st.warning("Nenhum dado encontrado para os filtros selecionados.")

# Código CSS final
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)