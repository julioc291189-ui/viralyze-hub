import streamlit as st
import pandas as pd
import json
import os
from scraper import scrape, COOKIES_FILE
from drive_exporter import format_ai_dossier, save_local_report

st.set_page_config(page_title="Viralyze Spy Hub", page_icon="⚡", layout="wide")

st.title("⚡ Viralyze TikTok Shop - Hub de Espionagem & IA")
st.caption("Mineração diária para Moda Feminina & Achadinhos | Formato POV com Influencer de IA")

if "products" not in st.session_state:
    st.session_state.products = []
if "debug_info" not in st.session_state:
    st.session_state.debug_info = None

tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard de Produtos", "🤖 Robô de Espionagem", "🚀 Dossiê para Agente de IA", "🔍 Diagnóstico da Tela"])

with tab2:
    st.subheader("Configurações do Robô Viralyze")
    
    col_auth1, col_auth2 = st.columns(2)
    with col_auth1:
        email = st.text_input("E-mail Viralyze:", placeholder="seu_email@exemplo.com")
    with col_auth2:
        password = st.text_input("Senha Viralyze:", type="password")

    cookies_exist = os.path.exists(COOKIES_FILE)
    if cookies_exist:
        st.success("✅ Cookies de sessão salvos!")
    else:
        st.info("ℹ️ Nenhum cookie salvo ainda. Insira e-mail e senha para o primeiro login.")

    if st.button("🚀 Iniciar Varredura de Produtos", type="primary"):
        with st.spinner("Robô acessando o Viralyze em segundo plano..."):
            try:
                res = scrape(email=email, password=password)
                if isinstance(res, tuple) and len(res) == 2:
                    data, debug_info = res
                elif isinstance(res, list):
                    data, debug_info = res, {}
                else:
                    data, debug_info = [], {}
                    
                st.session_state.products = data
                st.session_state.debug_info = debug_info
                
                if debug_info.get("error"):
                    st.error(f"Aviso no robô: {debug_info['error']}")
                elif data:
                    st.success(f"Varredura concluída! {len(data)} produtos carregados.")
                else:
                    st.warning("Varredura finalizada. Vá até a aba '🔍 Diagnóstico da Tela' para ver o print do que o robô encontrou.")
            except Exception as e:
                st.error(f"Erro na execução: {e}")

with tab4:
    st.subheader("O que o Robô está vendo na tela:")
    if st.session_state.debug_info:
        info = st.session_state.debug_info
        st.write(f"**URL Acessada:** `{info.get('url', 'N/A')}`")
        st.write(f"**Título da Página:** `{info.get('title', 'N/A')}`")
        if os.path.exists("debug_screen.png"):
            st.image("debug_screen.png", caption="Print tirado pelo robô no Viralyze", use_container_width=True)
        st.text_area("Texto capturado da página:", value=info.get("body", ""), height=200)
    else:
        st.info("Execute a varredura para visualizar a captura de tela do robô.")

with tab1:
    st.subheader("Produtos Minerados")
    if not st.session_state.products:
        st.info("Nenhum dado minerado ainda.")
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

with tab3:
    st.subheader("Exportar Relatório para Decisão de IA")
    if not st.session_state.products:
        st.warning("Minere os produtos primeiro para gerar o relatório.")
    else:
        dossier_text = format_ai_dossier(st.session_state.products)
        st.text_area("Prévia do Dossiê para a IA:", value=dossier_text, height=350)
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.download_button("📥 Baixar Dossiê (.md / Texto)", data=dossier_text, file_name="dossie_produtos_ia.md", mime="text/markdown")
        with col_d2:
            if st.button("☁️ Salvar e Sincronizar com Google Drive"):
                filename = save_local_report(dossier_text)
                st.success(f"Arquivo '{filename}' gerado com sucesso!")
