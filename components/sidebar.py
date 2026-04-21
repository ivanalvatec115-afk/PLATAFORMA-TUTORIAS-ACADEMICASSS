"""
components/sidebar.py
Barra lateral compartida para todos los dashboards.
"""
import streamlit as st
from utils.auth import logout, get_current_perfil


ROL_ICON = {
    "alumno": "🎓",
    "docente": "📚",
    "administrador": "⚙️",
}

ROL_LABEL = {
    "alumno": "Alumno",
    "docente": "Docente Tutor",
    "administrador": "Administrador",
}


def render_sidebar():
    perfil = get_current_perfil()
    if not perfil:
        return

    rol   = perfil.get("rol", "")
    icon  = ROL_ICON.get(rol, "👤")
    label = ROL_LABEL.get(rol, rol.capitalize())

    with st.sidebar:
        st.markdown(f"""
        <div style="text-align:center; padding: 1rem 0 0.5rem;">
            <div style="font-size:2.5rem;">{icon}</div>
            <div style="font-weight:700; font-size:1rem; margin-top:4px;">
                {perfil['nombre']} {perfil['apellido']}
            </div>
            <div style="font-size:0.78rem; opacity:0.7; margin-top:2px;">
                {label}
            </div>
        </div>
        <hr style="border-color:rgba(255,255,255,0.15); margin: 0.8rem 0;">
        """, unsafe_allow_html=True)

        st.markdown("### 🎓 SisTutor")

        # Menú según rol
        if rol == "alumno":
            _menu_alumno()
        elif rol == "docente":
            _menu_docente()
        elif rol == "administrador":
            _menu_admin()

        st.markdown("<hr style='border-color:rgba(255,255,255,0.15); margin-top:auto;'>",
                    unsafe_allow_html=True)

        if st.button("🚪 Cerrar sesión", use_container_width=True, type="secondary"):
            logout()
            st.switch_page("app.py")


def _menu_alumno():
    st.page_link("pages/alumno.py",   label="📅 Mi panel", icon=None)


def _menu_docente():
    st.page_link("pages/docente.py",  label="📅 Mi panel", icon=None)


def _menu_admin():
    st.page_link("pages/admin.py",    label="⚙️ Panel admin", icon=None)
