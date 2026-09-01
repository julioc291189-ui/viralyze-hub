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
    st.session_state.debug_info = {}

st.subheader("🤖 Robô de Espionagem Viralyze")

col_auth1, col_auth2 = st.columns(2)
with col_auth1:
    email = st.text_input("E-mail Viralyze:", value="julioc291189@gmail.com")
with col_auth2:
    password = st.text_input("Senha Viralyze:", type="password")

if st.button("🚀 Iniciar Varredura de Produtos", type="primary"):
    with st.spinner("Robô acessando o Viralyze em segundo plano e extraindo dados..."):
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
            
            if data:
                st.success(f"🎉 Varredura concluída! {len(data)} produtos encontrados.")
            else:
                st.warning("⚠️ O robô finalizou. Veja abaixo o print do que ele viu na tela.")
        except Exception as e:
            st.error(f"Erro na execução: {e}")

# 1. Exibe a captura de tela do robô direto na mesma página
if st.session_state.debug_info:
    info = st.session_state.debug_info
    st.markdown("---")
    st.subheader("🔍 O que o Robô viu na tela:")
    st.write(f"**URL:** `{info.get('url', 'N/A')}` | **Título:** `{info.get('title', 'N/A')}`")
    
    if os.path.exists("debug_screen.png"):
        st.image("debug_screen.png", caption="Captura da tela do Viralyze", use_container_width=True)
    
    with st.expander("Ver texto capturado da página"):
        st.text(info.get("body", "Sem texto capturado."))

# 2. Exibe os produtos minerados e o Dossiê para a IA
if st.session_state.products:
    st.markdown("---")
    st.subheader("📊 Produtos Minerados")
    df = pd.DataFrame(st.session_state.products)
    st.dataframe(df, use_container_width=True)
    
    st.markdown("---")
    st.subheader("🚀 Dossiê para Agente de IA")
    dossier_text = format_ai_dossier(st.session_state.products)
    st.text_area("Prévia do Dossiê para a IA:", value=dossier_text, height=300)
    st.download_button("📥 Baixar Dossiê (.md / Texto)", data=dossier_text, file_name="dossie_produtos_ia.md", mime="text/markdown")
