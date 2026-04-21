"""
pages/docente.py — Plataforma de Tutorías Académicas ITMH
"""
import streamlit as st
from datetime import datetime, date, time
from utils.styles import inject_css, estado_badge
from utils.auth import require_auth, get_current_perfil, get_current_rol
from utils.db import (
    get_disponibilidad_docente,
    agregar_disponibilidad,
    eliminar_disponibilidad,
    get_sesiones_docente,
    get_slots_pasados_docente,
    get_alumnos_por_slot,
    registrar_asistencia,
    get_materias_docente,
)
from components.sidebar import render_sidebar

st.set_page_config(page_title="Plataforma de Tutorías Académicas - ITMH · Docente",
                   page_icon="📚", layout="wide")
inject_css()
require_auth()

if get_current_rol() != "docente":
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
    <div><h2>📚 Panel del Docente <span class="role-tag">Docente Tutor</span></h2></div>
    <div class="user-info-txt">
        {perfil['nombre']} {perfil['apellido']} · {perfil.get('departamento','—')}
    </div>
</div>
""", unsafe_allow_html=True)

# ── Métricas ─────────────────────────────────────────────
sesiones    = get_sesiones_docente(perfil["id"])
total       = len(sesiones)
programadas = sum(1 for s in sesiones if s["estado"] == "Programada")
completadas = sum(1 for s in sesiones if s["estado"] == "Completada")
no_asistio  = sum(1 for s in sesiones if s["estado"] == "No asistió")

st.markdown(f"""
<div class="metric-row">
    <div class="metric-box"><div class="num">{total}</div><div class="lbl">Total sesiones</div></div>
    <div class="metric-box"><div class="num">{programadas}</div><div class="lbl">Programadas</div></div>
    <div class="metric-box"><div class="num">{completadas}</div><div class="lbl">Completadas</div></div>
    <div class="metric-box"><div class="num">{no_asistio}</div><div class="lbl">No asistió</div></div>
</div>
""", unsafe_allow_html=True)

col_left, col_right = st.columns([1, 1.3], gap="large")

# ── IZQUIERDA: Disponibilidad ─────────────────────────────
with col_left:
    st.markdown("<div class='tutoria-card'><h3>🕐 Gestionar disponibilidad</h3>", unsafe_allow_html=True)

    materias_doc = get_materias_docente(perfil["id"])
    if not materias_doc:
        st.warning("No tienes materias asignadas. Contacta al administrador.")
    else:
        with st.form("form_disponibilidad", clear_on_submit=True):
            mat_nombres = {m["nombre"]: m["id"] for m in materias_doc}
            mat_sel     = st.selectbox("Materia", list(mat_nombres.keys()))
            f_fecha     = st.date_input("Fecha", min_value=date.today())
            c1, c2      = st.columns(2)
            with c1:
                f_inicio = st.time_input("Hora inicio", value=time(9, 0))
            with c2:
                f_fin    = st.time_input("Hora fin",    value=time(10, 0))
            cupos    = st.number_input("Cupos máximos", min_value=1, max_value=8,
                                       value=8, step=1)
            submitted = st.form_submit_button("➕ Agregar bloque", type="primary",
                                              use_container_width=True)

        if submitted:
            if f_inicio >= f_fin:
                st.error("La hora de inicio debe ser menor a la de fin.")
            else:
                ok = agregar_disponibilidad(
                    perfil["id"], f_fecha, f_inicio, f_fin,
                    mat_nombres[mat_sel], cupos
                )
                if ok:
                    st.success("Bloque registrado.")
                    st.rerun()

    st.markdown("<b style='color:#0d2137; font-size:0.82rem;'>Mis horarios registrados</b>",
                unsafe_allow_html=True)
    slots = get_disponibilidad_docente(perfil["id"])
    if not slots:
        st.caption("Aún no has registrado disponibilidad.")
    else:
        for s in slots:
            libres     = s.get("cupos", 8) - s.get("cupos_usados", 0)
            estado_txt = f"✅ {libres} cupos libres" if s["disponible"] else "🔒 Sin cupos"
            col_info, col_btn = st.columns([3, 1])
            with col_info:
                st.markdown(f"""
                <div class="avail-item">
                    <div>
                        <strong>{s['fecha']} · {s.get('materia_nombre','—')}</strong><br>
                        <small>{s['hora_inicio'][:5]} – {s['hora_fin'][:5]} &nbsp; {estado_txt}</small>
                    </div>
                </div>""", unsafe_allow_html=True)
            with col_btn:
                if s.get("cupos_usados", 0) == 0:
                    if st.button("🗑", key=f"del_{s['id']}", help="Eliminar bloque"):
                        eliminar_disponibilidad(s["id"])
                        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# ── DERECHA: Tabs ────────────────────────────────────────
with col_right:
    tab_prog, tab_hist, tab_asist = st.tabs(
        ["📅 Programadas", "📋 Historial", "✍️ Registrar asistencia"]
    )

    # ── Tab: Programadas ──
    with tab_prog:
        progs = [s for s in sesiones if s["estado"] == "Programada"]
        if not progs:
            st.info("No tienes sesiones programadas.")
        else:
            for s in progs:
                nombre_alum = s.get("alumno_nombre", "—")
                ctrl        = s.get("alumno_control", "—")
                fh          = fmt_fecha(s["fecha_hora"])
                st.markdown(f"""
                <div class="avail-item">
                    <div>
                        <strong>{nombre_alum}</strong>
                        <small style="color:#5a7080"> · {ctrl}</small><br>
                        <small>📆 {fh} · 📖 {s.get('materia','—')}</small><br>
                        <small style="color:#888;">{s.get('descripcion','')}</small>
                    </div>
                    <span class="badge-blue">Programada</span>
                </div>""", unsafe_allow_html=True)

    # ── Tab: Historial ──
    with tab_hist:
        if not sesiones:
            st.info("Sin sesiones registradas.")
        else:
            filas = ""
            for s in sesiones:
                nombre_alum = s.get("alumno_nombre", "—")
                ctrl        = s.get("alumno_control", "—")
                fh          = fmt_fecha(s["fecha_hora"])
                mat         = s.get("materia") or "—"
                bdg         = estado_badge(s["estado"])
                filas += f"""
                <tr>
                    <td>{fh}</td>
                    <td>{nombre_alum}</td>
                    <td>{ctrl}</td>
                    <td>{mat}</td>
                    <td>{bdg}</td>
                </tr>"""
            st.markdown(f"""
            <table class="hist-table">
                <thead>
                    <tr><th>Fecha</th><th>Alumno</th><th>Control</th><th>Materia</th><th>Estado</th></tr>
                </thead>
                <tbody>{filas}</tbody>
            </table>""", unsafe_allow_html=True)

    # ── Tab: Registrar asistencia (solo sesiones PASADAS) ──
    with tab_asist:
        st.markdown("**Solo aparecen sesiones cuyo horario ya terminó.**")

        slots_pasados = get_slots_pasados_docente(perfil["id"])
        if not slots_pasados:
            st.info("No hay sesiones pasadas pendientes de registrar.")
        else:
            opciones_slot = {}
            for s in slots_pasados:
                label = (f"{s['fecha']} {s['hora_inicio'][:5]}–{s['hora_fin'][:5]}"
                         f" · {s.get('materia_nombre','—')}")
                opciones_slot[label] = s

            sel_label = st.selectbox("Selecciona la sesión", list(opciones_slot.keys()),
                                     key="slot_asist")
            slot_sel  = opciones_slot[sel_label]

            # Cargar todos los alumnos de ese slot
            alumnos_slot = get_alumnos_por_slot(slot_sel["id"])

            if not alumnos_slot:
                st.info("No hay alumnos registrados en esta sesión.")
            else:
                st.markdown(f"**{len(alumnos_slot)} alumno(s) reservaron este horario:**")
                st.divider()

                notas_globales = st.text_area(
                    "Notas generales de la sesión (opcional)",
                    placeholder="Temas tratados, observaciones generales…",
                    height=70, key="notas_glob"
                )

                cambios = {}
                for alumno in alumnos_slot:
                    sid   = alumno["id"]
                    nom   = alumno.get("alumno_nombre", "—")
                    ctrl  = alumno.get("alumno_control", "—")
                    ya_reg = alumno.get("asistencia") is not None

                    col_n, col_r = st.columns([2, 1])
                    with col_n:
                        st.markdown(f"""
                        <div style="padding:6px 0;">
                            <strong style="color:#0d2137;">{nom}</strong>
                            <small style="color:#5a7080;"> · {ctrl}</small>
                            {"&nbsp;<span class='badge-green'>Ya registrado</span>" if ya_reg else ""}
                        </div>""", unsafe_allow_html=True)
                    with col_r:
                        asistio = st.radio(
                            f"Asistencia",
                            ["✅ Asistió", "❌ No asistió"],
                            key=f"asist_{sid}",
                            horizontal=True,
                            index=0 if alumno.get("asistencia") is not False else 1,
                            label_visibility="collapsed"
                        )
                        cambios[sid] = asistio == "✅ Asistió"
                    st.divider()

                if st.button("💾 Guardar asistencias", type="primary",
                             use_container_width=True):
                    errores = 0
                    for sesion_id, asistio in cambios.items():
                        ok = registrar_asistencia(sesion_id, asistio, notas_globales)
                        if not ok:
                            errores += 1
                    if errores == 0:
                        st.success("✅ Asistencias guardadas correctamente.")
                        st.rerun()
                    else:
                        st.error(f"Hubo {errores} error(es) al guardar.")
