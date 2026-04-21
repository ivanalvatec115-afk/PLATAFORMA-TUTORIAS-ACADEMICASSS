"""
pages/alumno.py
Dashboard del Alumno — Plataforma de Tutorías Académicas - ITMH
"""
import streamlit as st
from datetime import datetime
from utils.styles import inject_css, estado_badge
from utils.auth import require_auth, get_current_perfil, get_current_rol
from utils.db import (
    get_disponibilidad_libre,
    agendar_sesion,
    cancelar_sesion,
    get_sesiones_alumno,
)
from components.sidebar import render_sidebar

st.set_page_config(page_title="Plataforma de Tutorías Académicas - ITMH · Alumno", page_icon="🎓", layout="wide")
inject_css()
require_auth()

if get_current_rol() != "alumno":
    st.error("Acceso restringido.")
    st.stop()

perfil = get_current_perfil()
render_sidebar()


def fmt_fecha(iso_str):
    try:
        return datetime.fromisoformat(iso_str.replace("Z", "+00:00")).strftime("%d/%m/%Y %H:%M")
    except Exception:
        return iso_str or "—"


# ── Header ───────────────────────────────────────────────
st.markdown(f"""
<div class="dash-header">
    <div><h2>🎓 Panel del Alumno <span class="role-tag">Alumno</span></h2></div>
    <div class="user-info-txt">
        {perfil['nombre']} {perfil['apellido']} · {perfil.get('numero_control','—')}
    </div>
</div>
""", unsafe_allow_html=True)

# ── Métricas ─────────────────────────────────────────────
sesiones    = get_sesiones_alumno(perfil["id"])
total       = len(sesiones)
programadas = sum(1 for s in sesiones if s["estado"] == "Programada")
completadas = sum(1 for s in sesiones if s["estado"] == "Completada")
canceladas  = sum(1 for s in sesiones if s["estado"] == "Cancelada")

st.markdown(f"""
<div class="metric-row">
    <div class="metric-box"><div class="num">{total}</div><div class="lbl">Total tutorías</div></div>
    <div class="metric-box"><div class="num">{programadas}</div><div class="lbl">Programadas</div></div>
    <div class="metric-box"><div class="num">{completadas}</div><div class="lbl">Completadas</div></div>
    <div class="metric-box"><div class="num">{canceladas}</div><div class="lbl">Canceladas</div></div>
</div>
""", unsafe_allow_html=True)

col_left, col_right = st.columns([1, 1.3], gap="large")

# ── IZQUIERDA ────────────────────────────────────────────
with col_left:

    # Disponibilidad de tutores
    st.markdown("<div class='tutoria-card'><h3>📅 Disponibilidad de tutores</h3>", unsafe_allow_html=True)
    slots = get_disponibilidad_libre()
    if not slots:
        st.info("No hay horarios disponibles por el momento.")
    else:
        for s in slots:
            # docente_nombre viene resuelto directamente desde db.py
            nombre_doc = s.get("docente_nombre", "").strip() or "Sin nombre"
            fecha  = s["fecha"]
            inicio = s["hora_inicio"][:5]
            fin    = s["hora_fin"][:5]
            st.markdown(f"""
            <div class="avail-item">
                <div>
                    <strong>{nombre_doc}</strong><br>
                    <small>📆 {fecha} &nbsp; 🕐 {inicio} – {fin}</small>
                </div>
                <span class="badge-green">Disponible</span>
            </div>
            """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    # Agendar sesión
    st.markdown("<div class='tutoria-card'><h3>➕ Agendar nueva sesión</h3>", unsafe_allow_html=True)
    slots_libres = get_disponibilidad_libre()

    if not slots_libres:
        st.warning("No hay horarios disponibles para agendar.")
    else:
        opciones = {}
        for s in slots_libres:
            nombre_doc = s.get("docente_nombre", "").strip() or "Sin nombre"
            label = f"{nombre_doc}  ·  {s['fecha']}  {s['hora_inicio'][:5]}–{s['hora_fin'][:5]}"
            opciones[label] = s

        sel_label   = st.selectbox("Selecciona horario disponible", list(opciones.keys()))
        sel_slot    = opciones[sel_label]
        materia     = st.text_input("Materia o tema", placeholder="Ej: Cálculo diferencial")
        descripcion = st.text_area("Descripción (opcional)",
                                   placeholder="Describe brevemente tu duda…", height=80)

        if st.button("✅ Solicitar tutoría", type="primary", use_container_width=True):
            if not materia:
                st.error("Indica la materia o tema.")
            else:
                fecha_hora = f"{sel_slot['fecha']}T{sel_slot['hora_inicio']}"
                ok = agendar_sesion(
                    alumno_id=perfil["id"],
                    docente_id=sel_slot["docente_id"],
                    disponibilidad_id=sel_slot["id"],
                    fecha_hora=fecha_hora,
                    materia=materia,
                    descripcion=descripcion,
                )
                if ok:
                    st.success("✅ ¡Tutoría agendada! Revisa tu historial.")
                    st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ── DERECHA: Historial ───────────────────────────────────
with col_right:
    st.markdown("<div class='tutoria-card'><h3>📋 Mi historial académico</h3>", unsafe_allow_html=True)

    if not sesiones:
        st.info("Aún no tienes tutorías registradas.")
    else:
        filas_html = ""
        for s in sesiones:
            # docente_nombre viene resuelto directamente desde db.py
            nombre_doc = s.get("docente_nombre", "").strip() or "Sin nombre"
            fh    = fmt_fecha(s["fecha_hora"])
            mat   = s.get("materia") or "—"
            badge = estado_badge(s["estado"])
            filas_html += f"""
            <tr>
                <td>{fh}</td>
                <td>{nombre_doc}</td>
                <td>{mat}</td>
                <td>{badge}</td>
            </tr>"""

        st.markdown(f"""
        <table class="hist-table">
            <thead>
                <tr><th>Fecha y hora</th><th>Docente</th><th>Materia</th><th>Estado</th></tr>
            </thead>
            <tbody>{filas_html}</tbody>
        </table>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
    st.divider()

    # Cancelar sesión
    programadas_list = [s for s in sesiones if s["estado"] == "Programada"]
    if programadas_list:
        st.markdown("<h4 style='color:#1e3a5f;'>❌ Cancelar una sesión</h4>", unsafe_allow_html=True)
        opciones_cancel = {
            f"{fmt_fecha(s['fecha_hora'])} · {s.get('materia','—')} · {s.get('docente_nombre','—')}": s
            for s in programadas_list
        }
        sel_cancel = st.selectbox("Selecciona la sesión a cancelar",
                                  list(opciones_cancel.keys()), key="cancel_sel")
        ses_cancel = opciones_cancel[sel_cancel]

        if st.button("Cancelar sesión", use_container_width=True):
            ok = cancelar_sesion(ses_cancel["id"], ses_cancel.get("disponibilidad_id"))
            if ok:
                st.success("Sesión cancelada.")
                st.rerun()
