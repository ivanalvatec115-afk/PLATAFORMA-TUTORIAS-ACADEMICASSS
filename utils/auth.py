"""
utils/auth.py
Funciones de autenticación y gestión de sesión con Supabase Auth.
"""
import streamlit as st
from utils.supabase_client import get_supabase


def login(correo: str, password: str) -> dict | None:
    """Intenta iniciar sesión. Retorna datos de sesión o None."""
    sb = get_supabase()
    try:
        res = sb.auth.sign_in_with_password({"email": correo, "password": password})
        if res.user:
            st.session_state["user"] = res.user
            st.session_state["session"] = res.session
            perfil = get_perfil(res.user.id)
            st.session_state["perfil"] = perfil
            return perfil
    except Exception as e:
        st.error(f"Error al iniciar sesión: {e}")
    return None


def register(nombre: str, apellido: str, correo: str, password: str,
             rol: str, numero_control: str = None, departamento: str = None) -> bool:
    """Registra un nuevo usuario en Supabase Auth + perfiles."""
    sb = get_supabase()
    try:
        res = sb.auth.sign_up({
            "email": correo,
            "password": password,
            "options": {
                "data": {
                    "nombre": nombre,
                    "apellido": apellido,
                    "rol": rol,
                }
            }
        })
        if res.user:
            # El trigger handle_new_user crea el perfil base;
            # actualizamos los campos extra
            sb.table("perfiles").update({
                "numero_control": numero_control,
                "departamento": departamento,
            }).eq("id", res.user.id).execute()
            return True
    except Exception as e:
        st.error(f"Error al registrar: {e}")
    return False


def logout():
    """Cierra la sesión actual."""
    sb = get_supabase()
    try:
        sb.auth.sign_out()
    except Exception:
        pass
    for key in ["user", "session", "perfil"]:
        st.session_state.pop(key, None)


def get_perfil(user_id: str) -> dict | None:
    """Obtiene el perfil del usuario desde la tabla perfiles."""
    sb = get_supabase()
    try:
        res = sb.table("perfiles").select("*").eq("id", user_id).single().execute()
        return res.data
    except Exception:
        return None


def require_auth():
    """Verifica si hay sesión activa. Redirige al login si no."""
    if "user" not in st.session_state or st.session_state["user"] is None:
        st.warning("Debes iniciar sesión para acceder a esta sección.")
        st.stop()


def get_current_perfil() -> dict | None:
    return st.session_state.get("perfil")


def get_current_rol() -> str | None:
    perfil = get_current_perfil()
    return perfil.get("rol") if perfil else None
