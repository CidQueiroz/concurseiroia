import streamlit as st
from streamlit_cookies_controller import CookieController

def get_cookie_controller():
    if "cookie_controller_instance" not in st.session_state:
        st.session_state["cookie_controller_instance"] = CookieController()
    return st.session_state["cookie_controller_instance"]
