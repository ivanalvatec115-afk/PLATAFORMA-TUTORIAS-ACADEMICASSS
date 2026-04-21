"""
utils/supabase_client.py
Conexion directa a Supabase con credenciales del proyecto.
"""
import streamlit as st
from supabase import create_client, Client

# Settings -> API -> Project URL
SUPABASE_URL = "https://jcyinyyymqlzfkzjbjbt.supabase.co/rest/v1/"

# Settings -> API -> anon public key (para operaciones normales)
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpjeWlueXl5bXFsemZrempiamJ0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY0NDUzODEsImV4cCI6MjA5MjAyMTM4MX0.eEgk6F4GEJBpgkg1v3udB9Fk1klz-1p-Ovf0NVeqtNo"

# Settings -> API -> service_role key (para crear/eliminar usuarios como admin)
# IMPORTANTE: nunca expongas esta key en el frontend público
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpjeWlueXl5bXFsemZrempiamJ0Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjQ0NTM4MSwiZXhwIjoyMDkyMDIxMzgxfQ.iPemvU8uylsNqk_fcFili_SAiEA9t5EXhTnuNZKDyGU"


@st.cache_resource
def get_supabase() -> Client:
    """Cliente normal con anon key (usuarios autenticados)."""
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


@st.cache_resource
def get_supabase_admin() -> Client:
    """Cliente con service_role key para operaciones de administración."""
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
