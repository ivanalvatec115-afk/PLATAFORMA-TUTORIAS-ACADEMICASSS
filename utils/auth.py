"""
utils/auth.py
Funciones de autenticacion y gestion de sesion con Supabase Auth.
"""
import streamlit as st
from utils.supabase_client import get_supabase


def login(correo: str, password: str) -> dict | None:
    """Intenta iniciar sesion. Retorna perfil o None."""
    sb = get_supabase()
    try:
        res = sb.auth.sign_in_with_password({"email": correo, "password": password})
        if res.user:
            st.session_state["user"] = res.user
            st.session_state["session"] = res.session
            perfil = get_perfil(res.user.id)
            if perfil is None:
                # El perfil no existe todavia, crearlo manualmente
                sb.table("perfiles").insert({
                    "id": res.user.id,
                    "nombre": res.user.user_metadata.get("nombre", "Usuario"),
                    "apellido": res.user.user_metadata.get("apellido", ""),
                    "correo": correo,
                    "rol": res.user.user_metadata.get("rol", "alumno"),
                }).execute()
                perfil = get_perfil(res.user.id)
            st.session_state["perfil"] = perfil
            return perfil
        else:
            st.error("No se pudo iniciar sesion. Verifica tus credenciales.")
    except Exception as e:
        msg = str(e)
        if "Email not confirmed" in msg:
            st.error("Debes confirmar tu correo antes de iniciar sesion. "
                     "Revisa tu bandeja de entrada o desactiva la confirmacion "
                     "en Supabase: Authentication → Settings → desactiva 'Enable email confirmations'.")
        elif "Invalid login credentials" in msg:
            st.error("Correo o contrasena incorrectos.")
        elif "Failed to fetch" in msg or "connection" in msg.lower():
            st.error("No se pudo conectar a la base de datos. "
                     "Verifica que SUPABASE_URL y SUPABASE_ANON_KEY sean correctos en supabase_client.py.")
        else:
            st.error(f"Error al iniciar sesion: {msg}")
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
            # Intentar actualizar campos extra si el trigger ya creo el perfil
            try:
                sb.table("perfiles").update({
                    "numero_control": numero_control,
                    "departamento": departamento,
                }).eq("id", res.user.id).execute()
            except Exception:
                pass
            return True
        else:
            st.error("No se pudo crear la cuenta. El correo puede estar en uso.")
    except Exception as e:
        msg = str(e)
        if "already registered" in msg or "already exists" in msg:
            st.error("Este correo ya esta registrado.")
        else:
            st.error(f"Error al registrar: {msg}")
    return False


def logout():
    """Cierra la sesion actual."""
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
    """Verifica si hay sesion activa. Detiene la pagina si no."""
    if "user" not in st.session_state or st.session_state["user"] is None:
        st.warning("Debes iniciar sesion para acceder a esta seccion.")
        st.stop()


def get_current_perfil() -> dict | None:
    return st.session_state.get("perfil")


def get_current_rol() -> str | None:
    perfil = get_current_perfil()
    return perfil.get("rol") if perfil else None
