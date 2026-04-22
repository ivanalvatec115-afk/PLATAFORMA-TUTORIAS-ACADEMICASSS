"""
pages/alumno.py — Plataforma de Tutorías Académicas ITMH
"""
import streamlit as st
from datetime import datetime
from utils.styles import inject_css, estado_badge
from utils.auth import require_auth, get_current_perfil, get_current_rol
from utils.db import (
    get_materias,
    get_disponibilidad_por_materia,
    agendar_sesion,
    cancelar_sesion,
    get_sesiones_alumno,
    CUPOS_MAX,
)
from components.sidebar import render_sidebar

st.set_page_config(page_title="Plataforma de Tutorías Académicas - ITMH · Alumno",
                   page_icon="🎓", layout="wide")
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

# ── IZQUIERDA: Agendar ───────────────────────────────────
with col_left:
    st.markdown("<div class='tutoria-card'><h3>➕ Agendar nueva sesión</h3>",
                unsafe_allow_html=True)

    materias       = get_materias()
    nombres_mat    = [m["nombre"] for m in materias]
    mat_sel_nombre = st.selectbox(
        "1️⃣ Selecciona la materia",
        options=[""] + nombres_mat,
        format_func=lambda x: "— Elige una materia —" if x == "" else x,
        key="mat_sel"
    )

    if mat_sel_nombre:
        mat_obj          = next((m for m in materias if m["nombre"] == mat_sel_nombre), None)
        slots_disponibles = get_disponibilidad_por_materia(mat_obj["id"]) if mat_obj else []

        if not slots_disponibles:
            st.info("No hay horarios disponibles para esta materia.")
        else:
            opciones_slot = {}
            for s in slots_disponibles:
                libres = s.get("cupos_libres", 0)
                label  = (f"{s['docente_nombre']}  ·  {s['fecha']}  "
                          f"{s['hora_inicio'][:5]}–{s['hora_fin'][:5]}  "
                          f"({libres}/{CUPOS_MAX} cupos libres)")
                opciones_slot[label] = s

            sel_label = st.selectbox("2️⃣ Selecciona horario",
                                     list(opciones_slot.keys()), key="slot_sel")
            sel_slot  = opciones_slot[sel_label]

            descripcion = st.text_area("Descripción (opcional)",
                                       placeholder="Describe brevemente tu duda…",
                                       height=80, key="desc_agendar")

            if st.button("✅ Solicitar tutoría", type="primary", use_container_width=True):
                fecha_hora = f"{sel_slot['fecha']}T{sel_slot['hora_inicio']}"
                ok = agendar_sesion(
                    alumno_id=perfil["id"],
                    docente_id=sel_slot["docente_id"],
                    disponibilidad_id=sel_slot["id"],
                    fecha_hora=fecha_hora,
                    materia=mat_sel_nombre,
                    descripcion=descripcion,
                )
                if ok:
                    st.success("✅ ¡Tutoría agendada correctamente!")
                    st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Cancelar sesión ──
    programadas_list = [s for s in sesiones if s["estado"] == "Programada"]
    if programadas_list:
        st.markdown("<div class='tutoria-card'><h3>❌ Cancelar una sesión</h3>",
                    unsafe_allow_html=True)
        opciones_cancel = {}
        for s in programadas_list:
            label = (f"{fmt_fecha(s['fecha_hora'])} · "
                     f"{s.get('materia','—')} · "
                     f"{s.get('docente_nombre','—')}")
            opciones_cancel[label] = s

        sel_cancel = st.selectbox("Selecciona la sesión a cancelar",
                                  list(opciones_cancel.keys()), key="cancel_sel")
        ses_cancel = opciones_cancel[sel_cancel]

        st.markdown(f"""
        <div class="avail-item">
            <div>
                <strong>{ses_cancel.get('materia','—')}</strong><br>
                <small>📆 {fmt_fecha(ses_cancel['fecha_hora'])} · 
                👨‍🏫 {ses_cancel.get('docente_nombre','—')}</small>
            </div>
        </div>""", unsafe_allow_html=True)

        if st.button("❌ Confirmar cancelación", use_container_width=True):
            # Obtener disponibilidad_id directamente del dict de la sesión
            disp_id = ses_cancel.get("disponibilidad_id")
            ok = cancelar_sesion(ses_cancel["id"], disp_id)
            if ok:
                st.success("✅ Sesión cancelada. El cupo fue liberado.")
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

# ── DERECHA: Historial ───────────────────────────────────
with col_right:
    st.markdown("<div class='tutoria-card'><h3>📋 Mi historial académico</h3>",
                unsafe_allow_html=True)

    if not sesiones:
        st.info("Aún no tienes tutorías registradas.")
    else:
        filas_html = ""
        for s in sesiones:
            nombre_doc = s.get("docente_nombre", "—")
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
        </table>""", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
