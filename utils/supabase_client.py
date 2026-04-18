"""
utils/supabase_client.py
Conexion directa a Supabase con credenciales del proyecto.
"""
import streamlit as st
from supabase import create_client, Client

# Reemplaza estos valores con los de tu proyecto en Supabase
# Settings -> API -> Project URL y anon public key
SUPABASE_URL = "https://jcyinyyymqlzfkzjbjbt.supabase.co/"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpjeWlueXl5bXFsemZrempiamJ0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY0NDUzODEsImV4cCI6MjA5MjAyMTM4MX0.eEgk6F4GEJBpgkg1v3udB9Fk1klz-1p-Ovf0NVeqtNo"


@st.cache_resource
def get_supabase() -> Client:
    """Retorna una instancia cacheada del cliente Supabase."""
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
