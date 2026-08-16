import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

import streamlit as st

def get_supabase() -> Client:
    # Se o cliente já existe na sessão do usuário, retorna ele
    if "supabase_client" in st.session_state:
        return st.session_state["supabase_client"]
        
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("SUPABASE_URL e SUPABASE_KEY devem estar configurados no .env")
    
    # Cria o cliente e salva na sessão do usuário atual
    client = create_client(url, key)
    
    # Se o usuário já tiver credenciais salvas (ex: sobreviveu a um hot reload), re-autentica
    if "user" in st.session_state and st.session_state["user"] is not None:
        from modules.cookies import get_cookie_controller
        cookie_controller = get_cookie_controller()
        creds = cookie_controller.get('concurso_session')
        if creds and isinstance(creds, dict) and creds.get("email") and creds.get("password"):
            try:
                client.auth.sign_in_with_password({"email": creds["email"], "password": creds["password"]})
            except:
                pass
                
    st.session_state["supabase_client"] = client
    return client
