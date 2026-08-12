import streamlit as st

DB_PATH = "data/bancos/db_novo.sqlite"

st.set_page_config(page_title="Concurseiro AI", layout="wide")

from modules import hoje, modo_prova, estatisticas, gerenciador, cronograma, diagnostico_ia

st.sidebar.title("Concurseiro AI 🎯")

with st.sidebar.expander("⚙️ Chaves de API (Opcional)"):
    st.markdown("Insira suas chaves para usar a IA (BYOK). Se deixar em branco, o sistema tentará usar as chaves padrão.")
    
    # Init session state if not exists
    if "user_groq_key" not in st.session_state:
        st.session_state["user_groq_key"] = ""
    if "user_gemini_key" not in st.session_state:
        st.session_state["user_gemini_key"] = ""
        
    st.session_state["user_groq_key"] = st.text_input("Groq API Key", type="password", value=st.session_state["user_groq_key"])
    st.session_state["user_gemini_key"] = st.text_input("Gemini API Key", type="password", value=st.session_state["user_gemini_key"])
    st.markdown("<small>[Como obter chave Groq?](https://console.groq.com/keys) | [Gemini?](https://aistudio.google.com/app/apikey)</small>", unsafe_allow_html=True)

menu = st.sidebar.radio("Navegação", ["Hoje", "Modo Prova", "Diagnóstico (IA)", "Estatísticas", "Gerenciador", "Cronograma"])

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
