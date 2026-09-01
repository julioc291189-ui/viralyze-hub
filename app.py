import streamlit as st
import pandas as pd
import json
import os
from scraper import scrape, COOKIES_FILE
from drive_exporter import format_ai_dossier, save_local_report

st.set_page_config(page_title="Viralyze Spy Hub", page_icon="⚡", layout="wide")

st.title("⚡ Viralyze TikTok Shop - Hub de Espionagem & IA")
st.caption("Mineração diária para Moda Feminina & Achadinhos | Formato POV com Influencer de IA")

# Inicializa sessão de dados
if "products" not in st.session_state:
    st.session_state.products = []

tab1, tab2, tab3 = st.tabs(["📊 Dashboard de Produtos", "🤖 Robô de Espionagem", "🚀 Dossiê para Agente de IA"])

# --- ABA 2: ROBÔ DE ESPIONAGEM ---
with tab2:
    st.subheader("Configurações do Robô Viralyze")
    
    col_auth1, col_auth2 = st.columns(2)
    with col_auth1:
        email = st.text_input("E-mail Viralyze:", placeholder="seu_email@exemplo.com")
    with col_auth2:
        password = st.text_input("Senha Viralyze:", type="password")

    cookies_exist = os.path.exists(COOKIES_FILE)
    if cookies_exist:
        st.success("✅ Cookies de sessão salvos! O robô pode entrar direto sem digitar login.")
    else:
        st.info("ℹ️ Nenhum cookie salvo ainda. Insira e-mail e senha para o primeiro login.")

    if st.button("🚀 Iniciar Varredura de Produtos", type="primary"):
        with st.spinner("Robô acessando o Viralyze em segundo plano e extraindo tendências..."):
            try:
                data = scrape(email=email, password=password)
                st.session_state.products = data
                st.success(f"Varredura concluída! {len(data)} produtos carregados.")
            except Exception as e:
                st.error(f"Erro na execução: {e}")

# --- ABA 1: DASHBOARD DE PRODUTOS ---
with tab1:
    st.subheader("Produtos Minerados")
    if not st.session_state.products:
        st.info("Nenhum dado minerado ainda. Vá até a aba 'Robô de Espionagem' para rodar a pesquisa.")
    else:
        df = pd.DataFrame(st.session_state.products)
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            categoria_filtro = st.multiselect("Filtrar por Categoria:", options=df["categoria"].unique(), default=df["categoria"].unique())
        with col_f2:
            busca = st.text_input("Buscar por termo/produto:")

        df_filtrado = df[df["categoria"].isin(categoria_filtro)]
        if busca:
            df_filtrado = df_filtrado[df_filtrado["titulo_bruto"].str.contains(busca, case=False)]

        st.dataframe(df_filtrado, use_container_width=True)

# --- ABA 3: DOSSIÊ PARA O AGENTE DE IA ---
with tab3:
    st.subheader("Exportar Relatório para Decisão de IA")
    if not st.session_state.products:
        st.warning("Minere os produtos primeiro para gerar o relatório.")
    else:
        dossier_text = format_ai_dossier(st.session_state.products)
        st.text_area("Prévia do Dossiê para a IA:", value=dossier_text, height=350)
        
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.download_button(
                label="📥 Baixar Dossiê (.md / Texto)",
                data=dossier_text,
                file_name="dossie_produtos_ia.md",
                mime="text/markdown"
            )
        with col_d2:
            if st.button("☁️ Salvar e Sincronizar com Google Drive"):
                filename = save_local_report(dossier_text)
                st.success(f"Arquivo '{filename}' gerado com sucesso!")
