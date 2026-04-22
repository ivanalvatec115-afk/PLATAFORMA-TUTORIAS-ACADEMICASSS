"""
pages/alumno.py — Plataforma de Tutorías Académicas ITMH
"""
import streamlit as st
from datetime import datetime
from utils.styles import inject_css, estado_badge
from utils.auth import require_auth, get_current_perfil, get_current_rol
from utils.reportes import reporte_alumno_excel, reporte_alumno_pdf
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

# Inicializar session_state para confirmación de cancelación
if "cancelar_sesion_id" not in st.session_state:
    st.session_state["cancelar_sesion_id"] = None
if "cancelar_disp_id" not in st.session_state:
    st.session_state["cancelar_disp_id"] = None


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

# ── Cargar sesiones ───────────────────────────────────────
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

# ── IZQUIERDA ─────────────────────────────────────────────
with col_left:

    # ── Agendar ──
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
        mat_obj           = next((m for m in materias if m["nombre"] == mat_sel_nombre), None)
        slots_disponibles = get_disponibilidad_por_materia(mat_obj["id"]) if mat_obj else []

        if not slots_disponibles:
            st.info("No hay horarios disponibles para esta materia.")
        else:
            opciones_slot = {}
            for s in slots_disponibles:
                label = (f"{s['docente_nombre']}  ·  {s['fecha']}  "
                         f"{str(s['hora_inicio'])[:5]}–{str(s['hora_fin'])[:5]}")
                opciones_slot[label] = s

            sel_label = st.selectbox("2️⃣ Selecciona horario",
                                     list(opciones_slot.keys()), key="slot_sel")
            sel_slot  = opciones_slot[sel_label]

            if st.button("✅ Solicitar tutoría", type="primary", use_container_width=True):
                fecha_hora = f"{sel_slot['fecha']}T{str(sel_slot['hora_inicio'])[:5]}"
                ok = agendar_sesion(
                    alumno_id        = perfil["id"],
                    docente_id       = sel_slot["docente_id"],
                    disponibilidad_id= sel_slot["id"],
                    fecha_hora       = fecha_hora,
                    materia          = mat_sel_nombre,
                    descripcion      = "",
                )
                if ok:
                    st.success("✅ ¡Tutoría agendada correctamente!")
                    st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Cancelar ──
    programadas_list = [s for s in sesiones if s["estado"] == "Programada"]
    if programadas_list:
        st.markdown("<div class='tutoria-card'><h3>❌ Cancelar una sesión</h3>",
                    unsafe_allow_html=True)

        for s in programadas_list:
            fh  = fmt_fecha(s["fecha_hora"])
            mat = s.get("materia", "—")
            doc = s.get("docente_nombre", "—")
            sid = s["id"]
            did = s.get("disponibilidad_id")

            col_info, col_btn = st.columns([3, 1])
            with col_info:
                st.markdown(f"""
                <div class="avail-item">
                    <div>
                        <strong>{mat}</strong><br>
                        <small>📆 {fh} · 👨‍🏫 {doc}</small>
                    </div>
                </div>""", unsafe_allow_html=True)
            with col_btn:
                if st.button("Cancelar", key=f"cancel_btn_{sid}",
                             use_container_width=True):
                    st.session_state["cancelar_sesion_id"] = sid
                    st.session_state["cancelar_disp_id"]   = did

        # Confirmación fuera del loop
        if st.session_state["cancelar_sesion_id"]:
            sid_conf = st.session_state["cancelar_sesion_id"]
            did_conf = st.session_state["cancelar_disp_id"]
            ses_conf = next((s for s in programadas_list if s["id"] == sid_conf), None)

            if ses_conf:
                st.warning(f"¿Confirmas cancelar la sesión de **{ses_conf.get('materia','—')}** "
                           f"el {fmt_fecha(ses_conf['fecha_hora'])}?")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ Sí, cancelar", type="primary",
                                 use_container_width=True, key="confirm_yes"):
                        ok = cancelar_sesion(sid_conf, did_conf)
                        if ok:
                            st.session_state["cancelar_sesion_id"] = None
                            st.session_state["cancelar_disp_id"]   = None
                            st.success("✅ Sesión cancelada. El cupo fue liberado.")
                            st.rerun()
                with c2:
                    if st.button("No, volver", use_container_width=True,
                                 key="confirm_no"):
                        st.session_state["cancelar_sesion_id"] = None
                        st.session_state["cancelar_disp_id"]   = None
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

# ── Descargar reporte ─────────────────────────────────────
if sesiones:
    with col_right:
        st.markdown("<div class='tutoria-card'><h3>📥 Descargar mi reporte</h3>",
                    unsafe_allow_html=True)
        nombre_completo = f"{perfil['nombre']} {perfil['apellido']}"
        col_xl, col_pdf = st.columns(2)
        with col_xl:
            try:
                datos, fname = reporte_alumno_excel(sesiones, nombre_completo)
                st.download_button(
                    "⬇️ Excel",
                    data=datos,
                    file_name=fname,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key="dl_alumno_xl"
                )
            except Exception as e:
                st.error(f"Error Excel: {e}")
        with col_pdf:
            try:
                datos, fname = reporte_alumno_pdf(sesiones, nombre_completo)
                st.download_button(
                    "⬇️ PDF",
                    data=datos,
                    file_name=fname,
                    mime="application/pdf",
                    use_container_width=True,
                    key="dl_alumno_pdf"
                )
            except Exception as e:
                st.error(f"Error PDF: {e}")
        st.markdown("</div>", unsafe_allow_html=True)
