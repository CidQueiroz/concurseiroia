__version__ = "1.5.0"
import streamlit as st
from backend.db import get_supabase

# Configuração da página e inicialização
st.set_page_config(page_title="AprovaTeck - Plataforma de Estudos Inteligente", layout="wide")
supabase = get_supabase()

import os
import json


from modules.cookies import get_cookie_controller

if "user" not in st.session_state:
    st.session_state["user"] = None

# Tenta carregar o cookie de sessão para auto-login se não estiver logado na memória
if st.session_state["user"] is None:
    cookie_controller = get_cookie_controller()
    creds = cookie_controller.get('aprovateck_session')
    if creds and isinstance(creds, dict) and creds.get("email") and creds.get("password"):
        try:
            res = supabase.auth.sign_in_with_password({"email": creds["email"], "password": creds["password"]})
            st.session_state["user"] = res.user
        except Exception:
            pass

def render_login():
    st.title("AprovaTeck 🎯")
    st.subheader("Plataforma de Estudos Inteligente")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2 = st.tabs(["Entrar", "Criar Conta"])
        
        with tab1:
            email = st.text_input("E-mail", key="login_email")
            senha = st.text_input("Senha", type="password", key="login_senha")
            if st.button("Acessar", type="primary", use_container_width=True):
                with st.spinner("Autenticando..."):
                    try:
                        res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
                        st.session_state["user"] = res.user
                        cookie_controller = get_cookie_controller()
                        cookie_controller.set('aprovateck_session', {"email": email, "password": senha})
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro no login. Verifique suas credenciais. Detalhes: {e}")
                        
        with tab2:
            email_cad = st.text_input("E-mail", key="cad_email")
            senha_cad = st.text_input("Senha", type="password", key="cad_senha")
            if st.button("Cadastrar", type="primary", use_container_width=True):
                with st.spinner("Criando conta..."):
                    try:
                        res = supabase.auth.sign_up({"email": email_cad, "password": senha_cad})
                        st.success("Conta criada com sucesso! Faça login na aba ao lado.")
                        st.info("Nota: Se você não desativou a confirmação de e-mail no Supabase, precisará confirmar sua caixa de entrada primeiro.")
                    except Exception as e:
                        st.error(f"Erro ao cadastrar: {e}")

if not st.session_state["user"]:
    render_login()
    st.stop() # Interrompe a execução aqui se não estiver logado

# ===============================
# ÁREA LOGADA
# ===============================
from modules import hoje, modo_prova, estatisticas, gerenciador, cronograma, diagnostico_ia

# Variável de compatibilidade para os módulos que ainda não foram refatorados
DB_PATH = "data/bancos/db_novo.sqlite"

st.sidebar.title("AprovaTeck 🎯")
st.sidebar.markdown(f"👤 **Logado:** {st.session_state['user'].email.split('@')[0]}")

bancas_disponiveis = ["CEBRASPE", "CESGRANRIO", "FCC", "FGV", "IBFC", "VUNESP", "Geral", "Outra..."]
banca_pref = st.session_state.get("banca_preferida", "Geral")

if banca_pref in bancas_disponiveis:
    banca_pref_index = bancas_disponiveis.index(banca_pref)
    banca_custom_default = ""
else:
    banca_pref_index = bancas_disponiveis.index("Outra...")
    banca_custom_default = banca_pref

banca_sel = st.sidebar.selectbox("🎯 Banca Preferida (IA)", bancas_disponiveis, index=banca_pref_index)

if banca_sel == "Outra...":
    banca_custom = st.sidebar.text_input("Digite o nome da Banca:", value=banca_custom_default)
    st.session_state["banca_preferida"] = banca_custom if banca_custom else "Geral"
else:
    st.session_state["banca_preferida"] = banca_sel

if st.sidebar.button("🚪 Sair da Conta", use_container_width=True):
    supabase.auth.sign_out()
    st.session_state["user"] = None
    cookie_controller = get_cookie_controller()
    cookie_controller.remove('aprovateck_session')
    st.rerun()

st.sidebar.markdown("---")

with st.sidebar.expander("⚙️ Chaves de API (Opcional)"):
    st.markdown("Insira suas chaves para usar a IA (BYOK). Se deixar em branco, o sistema tentará usar as chaves padrão.")
    
    cookie_controller = get_cookie_controller()
    saved_keys = cookie_controller.get('aprovateck_api_keys')
    
    if saved_keys and isinstance(saved_keys, dict):
        if not st.session_state.get("user_groq_key") and saved_keys.get("groq"):
            st.session_state["user_groq_key"] = saved_keys.get("groq")
        if not st.session_state.get("user_gemini_key") and saved_keys.get("gemini"):
            st.session_state["user_gemini_key"] = saved_keys.get("gemini")
            
    if "user_groq_key" not in st.session_state:
        st.session_state["user_groq_key"] = ""
    if "user_gemini_key" not in st.session_state:
        st.session_state["user_gemini_key"] = ""
        
    def save_keys():
        cookie_controller.set('aprovateck_api_keys', {
            "groq": st.session_state.get("user_groq_key", ""),
            "gemini": st.session_state.get("user_gemini_key", "")
        })

    st.text_input("Groq API Key", type="password", key="user_groq_key", on_change=save_keys)
    st.text_input("Gemini API Key", type="password", key="user_gemini_key", on_change=save_keys)
    st.markdown("<small>[Como obter chave Groq?](https://console.groq.com/keys) | [Gemini?](https://aistudio.google.com/app/apikey)</small>", unsafe_allow_html=True)

    opcoes_menu = ["Hoje", "Modo Prova", "Diagnóstico (IA)", "Estatísticas", "Cronograma"]
    if st.session_state["user"].email == "cydy.potter@gmail.com":
        opcoes_menu.insert(4, "Gerenciador")
        
    menu = st.sidebar.radio("Navegação", opcoes_menu)

if menu == "Hoje":
    hoje.render(DB_PATH)
elif menu == "Modo Prova":
    modo_prova.render(DB_PATH)
elif menu == "Diagnóstico (IA)":
    diagnostico_ia.render(DB_PATH)
elif menu == "Estatísticas":
    estatisticas.render(DB_PATH)
elif menu == "Gerenciador":
    gerenciador.render(DB_PATH)
elif menu == "Cronograma":
    cronograma.render(DB_PATH)
