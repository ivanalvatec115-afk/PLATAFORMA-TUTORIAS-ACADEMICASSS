"""
app.py — Punto de entrada de SisTutor
Plataforma de Tutorias Academicas · Instituto Tecnologico de Matehuala
"""
import streamlit as st
from utils.styles import inject_css
from utils.auth import login, get_current_rol
from utils.supabase_client import get_supabase, SUPABASE_URL

st.set_page_config(
    page_title="SisTutor · Tutorías Académicas",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_css()


def redirect_by_role():
    rol = get_current_rol()
    if rol == "alumno":
        st.switch_page("pages/alumno.py")
    elif rol == "docente":
        st.switch_page("pages/docente.py")
    elif rol == "administrador":
        st.switch_page("pages/admin.py")


# Si ya hay sesion activa, redirigir
if "user" in st.session_state and st.session_state["user"]:
    redirect_by_role()

# ── Layout ───────────────────────────────────────────────
col_brand, col_form = st.columns([1.2, 1], gap="large")

with col_brand:
    st.markdown("""
    <div class="login-brand">
        <div style="font-size:3.5rem; margin-bottom:1.2rem;">🎓</div>
        <h1>SisTutor</h1>
        <p>Plataforma centralizada para gestionar disponibilidad,
        agendar sesiones y dar seguimiento académico a las tutorías
        del Instituto Tecnológico de Matehuala.</p>
        <div class="feature">✅ Gestión de disponibilidad docente</div>
        <div class="feature">📅 Agendamiento de sesiones</div>
        <div class="feature">📊 Reportes y estadísticas</div>
        <div class="feature">🔔 Control de asistencia</div>
        <div style="margin-top:2rem; padding-top:1.2rem;
                    border-top:1px solid rgba(255,255,255,0.2);
                    font-size:0.78rem; opacity:0.7;">
            Instituto Tecnológico de Matehuala<br>
            Ingeniería en Sistemas Computacionales · 6SA
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("🔌 Verificar conexión a Supabase"):
        st.caption(f"URL: `{SUPABASE_URL}`")
        if st.button("Probar conexión", use_container_width=True):
            try:
                sb = get_supabase()
                sb.table("perfiles").select("id").limit(1).execute()
                st.success("✅ Conexión exitosa.")
            except Exception as e:
                st.error(f"❌ Error: {e}")

with col_form:
    st.markdown("""
    <div class="login-box">
        <h2>Iniciar sesión</h2>
        <p>Accede con tu correo institucional y contraseña.</p>
    </div>
    """, unsafe_allow_html=True)

    correo   = st.text_input("Correo institucional",
                             placeholder="usuario@itm.edu.mx",
                             key="login_correo")
    password = st.text_input("Contraseña", type="password", key="login_pass")

    if st.button("Ingresar →", type="primary", use_container_width=True):
        if not correo or not password:
            st.error("Completa todos los campos.")
        else:
            with st.spinner("Verificando credenciales…"):
                perfil = login(correo, password)
            if perfil:
                st.success(f"¡Bienvenido/a, {perfil['nombre']}!")
                st.rerun()

    st.markdown("""
    <div class="login-note">
        🔒 El acceso es exclusivo para usuarios registrados por el administrador.
    </div>
    """, unsafe_allow_html=True)
