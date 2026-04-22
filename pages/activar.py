"""
pages/activar.py
P�gina de activación de cuenta.
Captura el token del fragmento # via JavaScript y lo pasa como query param.
"""
import streamlit as st
import streamlit.components.v1 as components
from utils.styles import inject_css
from utils.supabase_client import get_supabase, SUPABASE_URL, SUPABASE_ANON_KEY

st.set_page_config(
    page_title="Activar cuenta — Tutorías ITMH",
    page_icon="🎓",
    layout="centered",
)
inject_css()

params = st.query_params
token  = params.get("token", "")
tipo   = params.get("type", "")

# ── Si no hay token en query params, inyectar JS para leer el fragmento # ──
if not token:
    # Este componente JS lee el hash de la URL y recarga con ?token=...&type=...
    components.html("""
    <script>
    (function() {
        const hash = window.location.hash.substring(1);
        if (!hash) return;
        const params = new URLSearchParams(hash);
        const token = params.get('access_token') || params.get('token');
        const type  = params.get('type') || 'invite';
        if (token) {
            const base = window.location.origin + window.location.pathname;
            window.location.replace(base + '?token=' + token + '&type=' + type);
        }
    })();
    </script>
    <p style="font-family:sans-serif; color:#555; text-align:center; margin-top:2rem;">
        Cargando activación de cuenta…
    </p>
    """, height=80)

    st.markdown("""
    <div style="text-align:center; margin-top:2rem;">
        <div style="font-size:2rem;">🎓</div>
        <p style="color:#3d5166;">Procesando tu invitación, espera un momento…</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Si ya tenemos el token, mostrar formulario ────────────
st.markdown("""
<div class="login-brand" style="text-align:center; margin-bottom:2rem;">
    <div style="font-size:3rem; color:#ffffff !important;">🎓</div>
    <h1 style="color:#ffffff !important;">Activar cuenta</h1>
    <p style="color:#ffffff !important;">
        Plataforma de Tutorías Académicas · ITMH
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="tutoria-card">
    <h3>🔑 Crea tu contraseña</h3>
    <p style="color:#3d5166; font-size:0.9rem;">
        Elige una contraseña segura de al menos 6 caracteres para acceder al sistema.
    </p>
</div>
""", unsafe_allow_html=True)

with st.form("form_activar"):
    nueva_pass  = st.text_input("Nueva contraseña *", type="password",
                                 placeholder="Mínimo 6 caracteres")
    nueva_pass2 = st.text_input("Confirmar contraseña *", type="password",
                                 placeholder="Repite la contraseña")
    activar     = st.form_submit_button("✅ Activar mi cuenta", type="primary",
                                         use_container_width=True)

if activar:
    if not nueva_pass or not nueva_pass2:
        st.error("Completa ambos campos.")
    elif nueva_pass != nueva_pass2:
        st.error("Las contraseñas no coinciden.")
    elif len(nueva_pass) < 6:
        st.error("La contraseña debe tener al menos 6 caracteres.")
    else:
        with st.spinner("Activando tu cuenta…"):
            try:
                sb = get_supabase()
                # Verificar el token OTP
                res = sb.auth.verify_otp({
                    "token_hash": token,
                    "type":       "invite",
                })
                if res.session:
                    # Con la sesión activa, actualizar contraseña
                    sb.auth.update_user({"password": nueva_pass})
                    st.success("✅ ¡Cuenta activada! Ya puedes iniciar sesión.")
                    st.markdown("""
                    <div style="text-align:center; margin-top:1.5rem;">
                        <a href="/" style="
                            background:#1a6fa8; color:white; padding:10px 28px;
                            border-radius:10px; text-decoration:none;
                            font-weight:700; font-size:0.95rem;">
                            Ir al inicio de sesión →
                        </a>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error("No se pudo verificar el token. Puede haber expirado. "
                             "Pide al administrador que reenvíe la invitación.")
            except Exception as e:
                err = str(e)
                if "expired" in err.lower() or "invalid" in err.lower():
                    st.error("El link de activación expiró o ya fue usado. "
                             "Solicita al administrador que reenvíe la invitación.")
                else:
                    st.error(f"Error al activar: {err}")
