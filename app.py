"""
app.py  — Punto de entrada de TutorIA
Plataforma de Tutorías Académicas · Instituto Tecnológico de Matehuala
"""
import streamlit as st
from utils.styles import inject_css
from utils.auth import login, register, logout, get_current_rol, get_current_perfil

# ── Configuración de página ──────────────────────────────
st.set_page_config(
    page_title="TutorIA · Tutorías Académicas",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="auto",
)

inject_css()


# ── Redirección según rol ────────────────────────────────
def redirect_by_role():
    rol = get_current_rol()
    if rol == "alumno":
        st.switch_page("pages/alumno.py")
    elif rol == "docente":
        st.switch_page("pages/docente.py")
    elif rol == "administrador":
        st.switch_page("pages/admin.py")


# Si ya hay sesión activa, redirigir directamente
if "user" in st.session_state and st.session_state["user"]:
    redirect_by_role()

# ── Pantalla de Login / Registro ─────────────────────────
col_brand, col_form = st.columns([1.3, 1], gap="large")

with col_brand:
    st.markdown("""
    <div class="login-brand">
        <div style="font-size:3rem; margin-bottom:1rem;">🎓</div>
        <h1>TutorIA</h1>
        <p>Plataforma centralizada para gestionar disponibilidad, agendar sesiones
        y dar seguimiento académico a las tutorías institucionales.</p>
        <div class="feature">✅ Trazabilidad de requisitos</div>
        <div class="feature">📅 Calendario interactivo</div>
        <div class="feature">📊 Reportes y estadísticas</div>
        <div class="feature">🔔 Control de asistencia</div>
        <br>
        <p style="opacity:0.6; font-size:0.78rem;">
            Instituto Tecnológico de Matehuala<br>
            Ingeniería en Sistemas Computacionales
        </p>
    </div>
    """, unsafe_allow_html=True)

with col_form:
    tab_login, tab_reg = st.tabs(["🔑 Iniciar sesión", "📝 Registrarse"])

    # ── TAB LOGIN ──
    with tab_login:
        st.markdown("#### Acceder a la plataforma")
        correo = st.text_input("Correo institucional", placeholder="usuario@instituto.edu.mx",
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
                else:
                    st.error("Correo o contraseña incorrectos.")

    # ── TAB REGISTRO ──
    with tab_reg:
        st.markdown("#### Crear cuenta nueva")
        r_nombre   = st.text_input("Nombre(s)", key="reg_nombre")
        r_apellido = st.text_input("Apellidos", key="reg_apellido")
        r_correo   = st.text_input("Correo institucional", key="reg_correo")
        r_pass     = st.text_input("Contraseña (mín. 6 caracteres)", type="password", key="reg_pass")
        r_pass2    = st.text_input("Confirmar contraseña", type="password", key="reg_pass2")
        r_rol      = st.selectbox("Rol", ["alumno", "docente"], key="reg_rol")

        r_control = r_depto = None
        if r_rol == "alumno":
            r_control = st.text_input("Número de control", key="reg_control")
        else:
            r_depto = st.text_input("Departamento / Área", key="reg_depto")

        if st.button("Crear cuenta", type="primary", use_container_width=True):
            if not all([r_nombre, r_apellido, r_correo, r_pass, r_pass2]):
                st.error("Completa todos los campos.")
            elif r_pass != r_pass2:
                st.error("Las contraseñas no coinciden.")
            elif len(r_pass) < 6:
                st.error("La contraseña debe tener al menos 6 caracteres.")
            else:
                with st.spinner("Creando cuenta…"):
                    ok = register(r_nombre, r_apellido, r_correo, r_pass,
                                  r_rol, r_control, r_depto)
                if ok:
                    st.success("¡Cuenta creada! Revisa tu correo para confirmar y luego inicia sesión.")
                else:
                    st.error("No se pudo crear la cuenta. El correo puede estar en uso.")
