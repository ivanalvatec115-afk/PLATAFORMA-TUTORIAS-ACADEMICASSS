"""
utils/supabase_client.py
Inicializa el cliente de Supabase usando variables de entorno de Streamlit Secrets.
"""
import streamlit as st
from supabase import create_client, Client


@st.cache_resource
def get_supabase() -> Client:
    """Retorna una instancia cacheada del cliente Supabase."""
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_ANON_KEY"]
    return create_client(url, key)
