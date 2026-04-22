"""
pages/activar.py
P¡gina de activaciÃ³n de cuenta para nuevos usuarios.
El usuario llega aquÃ­ desde el link del correo de invitaciÃ³n.
Supabase redirige con: ?token=xxx&type=invite
"""
import streamlit as st
from utils.styles import inject_css
from utils.supabase_client import get_supabase

st.set_page_config(
    page_title="Activar cuenta â Plataforma de TutorÃ­as ITMH",
    page_icon="ð",
    layout="centered",
)
inject_css()

# ââ Leer token de la URL ââââââââââââââââââââââââââââââââââ
params = st.query_params
token  = params.get("token", "")
tipo   = params.get("type", "")

# ââ UI âââââââââââââââââââââââââââââââââââââââââââââââââââ
st.markdown("""
<div style="max-width:480px; margin:3rem auto;">
<div class="login-brand" style="text-align:center; margin-bottom:2rem;">
    <div style="font-size:3rem;">ð</div>
    <h1 style="color:#ffffff !important;">Activar cuenta</h1>
    <p style="color:#ffffff !important;">
        Plataforma de TutorÃ­as AcadÃ©micas Â· ITMH
    </p>
</div>
""", unsafe_allow_html=True)

if not token:
    st.error("â Link invÃ¡lido o expirado. Solicita al administrador que reenvÃ­e la invitaciÃ³n.")
    st.stop()

st.markdown("""
<div class="tutoria-card">
    <h3>ð Crea tu contraseÃ±a</h3>
    <p style="color:#3d5166; font-size:0.9rem;">
        Elige una contraseÃ±a segura de al menos 6 caracteres para acceder al sistema.
    </p>
</div>
""", unsafe_allow_html=True)

with st.form("form_activar"):
    nueva_pass  = st.text_input("Nueva contraseÃ±a *", type="password",
                                 placeholder="MÃ­nimo 6 caracteres")
    nueva_pass2 = st.text_input("Confirmar contraseÃ±a *", type="password",
                                 placeholder="Repite la contraseÃ±a")
    activar     = st.form_submit_button("â Activar mi cuenta", type="primary",
                                         use_container_width=True)

if activar:
    if not nueva_pass or not nueva_pass2:
        st.error("Completa ambos campos.")
    elif nueva_pass != nueva_pass2:
        st.error("Las contraseÃ±as no coinciden.")
    elif len(nueva_pass) < 6:
        st.error("La contraseÃ±a debe tener al menos 6 caracteres.")
    else:
        with st.spinner("Activando tu cuentaâ¦"):
            try:
                sb  = get_supabase()
                # Verificar el token OTP de invitaciÃ³n
                res = sb.auth.verify_otp({
                    "token_hash": token,
                    "type":       "invite",
                })
                if res.session:
                    # Actualizar contraseÃ±a con la sesiÃ³n reciÃ©n establecida
                    sb.auth.update_user({"password": nueva_pass})
                    st.success("â Â¡Cuenta activada correctamente! Ya puedes iniciar sesiÃ³n.")
                    st.markdown("""
                    <div style="text-align:center; margin-top:1.5rem;">
                        <a href="/" style="
                            background:#1a6fa8; color:white; padding:10px 28px;
                            border-radius:10px; text-decoration:none;
                            font-weight:700; font-size:0.95rem;">
                            Ir al inicio de sesiÃ³n â
                        </a>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error("No se pudo verificar el token. Puede haber expirado.")
            except Exception as e:
                st.error(f"Error al activar la cuenta: {e}")

st.markdown("</div>", unsafe_allow_html=True)
