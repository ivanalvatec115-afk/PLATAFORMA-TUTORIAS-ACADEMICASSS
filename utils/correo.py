"""
utils/correo.py
Envío de correos via Gmail SMTP con credenciales hardcodeadas.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

GMAIL_USER = "tutoriasacademicasitmh@gmail.com"
GMAIL_PASS = "hdhs ekow rgra jiff"
REMITENTE  = "Plataforma de Tutorías ITMH <tutoriasacademicasitmh@gmail.com>"


def enviar_credenciales(correo_destino: str, nombre: str,
                        correo_usuario: str, password: str) -> tuple[bool, str]:
    """Envía correo con credenciales de acceso al usuario."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Acceso a la Plataforma de Tutorías Académicas - ITMH"
        msg["From"]    = REMITENTE
        msg["To"]      = correo_destino

        cuerpo_html = f"""
        <html><body style="font-family:Arial,sans-serif; color:#0d1f2d; max-width:600px; margin:auto;">
            <div style="background:#0d2137; padding:24px; border-radius:12px 12px 0 0; text-align:center;">
                <h1 style="color:#ffffff; margin:0; font-size:1.5rem;">🎓 Plataforma de Tutorías Académicas</h1>
                <p style="color:#a8c8e8; margin:6px 0 0;">Instituto Tecnológico de Matehuala</p>
            </div>
            <div style="background:#f8fbff; padding:28px; border:1px solid #cdd8e3; border-radius:0 0 12px 12px;">
                <p>Hola <strong>{nombre}</strong>,</p>
                <p>Tu cuenta en la Plataforma de Tutorías Académicas ha sido creada. 
                   Aquí están tus credenciales de acceso:</p>

                <div style="background:#ffffff; border:1px solid #cdd8e3; border-radius:10px;
                            padding:20px; margin:20px 0; text-align:center;">
                    <p style="margin:0 0 4px; color:#5a7080; font-size:0.85rem;">USUARIO (correo institucional)</p>
                    <p style="margin:0 0 4px; font-size:1.1rem; font-weight:bold; color:#0d2137;">
                        {correo_usuario}
                    </p>
                    <p style="margin:0 0 16px; color:#e74c3c; font-size:0.78rem;">
                        ⚠️ Este correo es tu nombre de usuario para iniciar sesión
                    </p>
                    <p style="margin:0 0 8px; color:#5a7080; font-size:0.85rem;">CONTRASEÑA TEMPORAL</p>
                    <p style="margin:0; font-size:1.3rem; font-weight:bold; color:#1a6fa8;
                               letter-spacing:2px; font-family:monospace;">
                        {password}
                    </p>
                </div>

                <p style="color:#e74c3c; font-size:0.88rem;">
                    ⚠️ Por seguridad, cambia tu contraseña después de tu primer inicio de sesión
                    desde la sección de configuración de tu perfil.
                </p>

                <div style="background:#eef2ff; border-radius:8px; padding:14px; margin:16px 0; text-align:center;">
                    <p style="margin:0; color:#0d2137; font-size:0.88rem;">
                        🌐 Accede a la plataforma en:<br>
                        <strong>plataforma-tutorias-academicasss-jze9ktp9wvmmegae8tpv2i.streamlit.app</strong>
                    </p>
                </div>

                <hr style="border:none; border-top:1px solid #e2e8f0; margin:20px 0;">
                <p style="color:#5a7080; font-size:0.78rem; text-align:center; margin:0;">
                    Este correo fue enviado automáticamente por la Plataforma de Tutorías Académicas.<br>
                    Instituto Tecnológico de Matehuala · Ingeniería en Sistemas Computacionales
                </p>
            </div>
        </body></html>
        """

        cuerpo_txt = (
            f"Hola {nombre},\n\n"
            f"Tu cuenta ha sido creada en la Plataforma de Tutorías Académicas - ITMH.\n\n"
            f"USUARIO (correo institucional): {correo_usuario}\n"
            f"CONTRASEÑA TEMPORAL: {password}\n\n"
            f"IMPORTANTE: El correo institucional es tu nombre de usuario para iniciar sesión.\n\n"
            f"Plataforma: plataforma-tutorias-academicasss-jze9ktp9wvmmegae8tpv2i.streamlit.app\n\n"
            f"Por seguridad, cambia tu contraseña después de tu primer inicio de sesión.\n\n"
            f"Instituto Tecnológico de Matehuala"
        )

        msg.attach(MIMEText(cuerpo_txt, "plain"))
        msg.attach(MIMEText(cuerpo_html, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(GMAIL_USER, GMAIL_PASS)
            smtp.sendmail(GMAIL_USER, correo_destino, msg.as_string())

        return True, "Correo enviado."
    except Exception as e:
        return False, str(e)
