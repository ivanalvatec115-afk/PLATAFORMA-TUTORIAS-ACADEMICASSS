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
    get_slots_con_alumnos_docente,
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


def fmt_fecha_slot(fecha, h_ini, h_fin):
    try:
        d = datetime.strptime(fecha, "%Y-%m-%d").strftime("%d/%m/%Y")
        return f"{d}  {h_ini[:5]} – {h_fin[:5]}"
    except Exception:
        return f"{fecha} {h_ini[:5]}–{h_fin[:5]}"


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
slots_prog  = get_slots_con_alumnos_docente(perfil["id"], solo_pasados=False)
slots_pas   = get_slots_con_alumnos_docente(perfil["id"], solo_pasados=True)
tot_prog    = sum(len(s["alumnos"]) for s in slots_prog)
tot_comp    = sum(1 for s in slots_pas for a in s["alumnos"] if a.get("estado") == "Completada")
tot_noa     = sum(1 for s in slots_pas for a in s["alumnos"] if a.get("estado") == "No asistió")
tot_slots   = len(slots_prog) + len(slots_pas)

st.markdown(f"""
<div class="metric-row">
    <div class="metric-box"><div class="num">{tot_slots}</div><div class="lbl">Bloques totales</div></div>
    <div class="metric-box"><div class="num">{tot_prog}</div><div class="lbl">Alumnos programados</div></div>
    <div class="metric-box"><div class="num">{tot_comp}</div><div class="lbl">Completadas</div></div>
    <div class="metric-box"><div class="num">{tot_noa}</div><div class="lbl">No asistió</div></div>
</div>
""", unsafe_allow_html=True)

col_left, col_right = st.columns([1, 1.4], gap="large")

# ── IZQUIERDA: Disponibilidad ─────────────────────────────
with col_left:
    st.markdown("<div class='tutoria-card'><h3>🕐 Gestionar disponibilidad</h3>", unsafe_allow_html=True)

    materias_doc = get_materias_docente(perfil["id"])
    if not materias_doc:
        st.warning("No tienes materias asignadas. Contacta al administrador.")
    else:
        with st.form("form_disp", clear_on_submit=True):
            mat_nombres = {m["nombre"]: m["id"] for m in materias_doc}
            mat_sel     = st.selectbox("Materia", list(mat_nombres.keys()))
            f_fecha     = st.date_input("Fecha", min_value=date.today())
            c1, c2      = st.columns(2)
            with c1: f_inicio = st.time_input("Hora inicio", value=time(9, 0))
            with c2: f_fin    = st.time_input("Hora fin",    value=time(10, 0))
            cupos     = st.number_input("Cupos máximos", min_value=1, max_value=8, value=8)
            submitted = st.form_submit_button("➕ Agregar bloque", type="primary",
                                              use_container_width=True)
        if submitted:
            if f_inicio >= f_fin:
                st.error("La hora inicio debe ser menor a la de fin.")
            else:
                ok = agregar_disponibilidad(perfil["id"], f_fecha, f_inicio, f_fin,
                                            mat_nombres[mat_sel], cupos)
                if ok:
                    st.success("Bloque registrado.")
                    st.rerun()

    st.markdown("<b style='color:#0d2137; font-size:0.82rem;'>Mis bloques registrados</b>",
                unsafe_allow_html=True)
    slots_todos = get_disponibilidad_docente(perfil["id"])
    if not slots_todos:
        st.caption("Aún no has registrado disponibilidad.")
    else:
        for s in slots_todos:
            libres     = s.get("cupos", 8) - s.get("cupos_usados", 0)
            estado_txt = f"✅ {libres} cupos libres" if s["disponible"] else "🔒 Sin cupos"
            col_i, col_b = st.columns([3, 1])
            with col_i:
                st.markdown(f"""
                <div class="avail-item">
                    <div>
                        <strong>{s['fecha']} · {s.get('materia_nombre','—')}</strong><br>
                        <small>{s['hora_inicio'][:5]} – {s['hora_fin'][:5]} &nbsp; {estado_txt}</small>
                    </div>
                </div>""", unsafe_allow_html=True)
            with col_b:
                if s.get("cupos_usados", 0) == 0:
                    if st.button("🗑", key=f"del_{s['id']}", help="Eliminar"):
                        eliminar_disponibilidad(s["id"])
                        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ── DERECHA: Tabs ─────────────────────────────────────────
with col_right:
    tab_prog_t, tab_pas_t = st.tabs(["📅 Sesiones programadas", "✍️ Registrar asistencia"])

    # ── Tab: SESIONES PROGRAMADAS (bloques futuros) ──
    with tab_prog_t:
        if not slots_prog:
            st.info("No tienes sesiones programadas próximas.")
        else:
            for slot in slots_prog:
                titulo = fmt_fecha_slot(slot["fecha"], slot["hora_inicio"], slot["hora_fin"])
                mat    = slot.get("materia_nombre", "—")
                usados = slot.get("cupos_usados", 0)
                cupos  = slot.get("cupos", 8)
                alumnos = slot["alumnos"]

                with st.expander(f"📆 {titulo}  ·  📖 {mat}  ·  👥 {usados}/{cupos} alumnos"):
                    if not alumnos:
                        st.caption("Ningún alumno ha reservado este bloque aún.")
                    else:
                        filas = ""
                        for a in alumnos:
                            bdg   = estado_badge(a.get("estado", "Programada"))
                            filas += f"""<tr>
                                <td>{a.get('alumno_nombre','—')}</td>
                                <td>{a.get('alumno_control','—')}</td>
                                <td>{bdg}</td>
                            </tr>"""
                        st.markdown(f"""
                        <table class="hist-table">
                            <thead><tr><th>Alumno</th><th>No. Control</th><th>Estado</th></tr></thead>
                            <tbody>{filas}</tbody>
                        </table>""", unsafe_allow_html=True)

    # ── Tab: REGISTRAR ASISTENCIA (bloques ya pasados) ──
    with tab_pas_t:
        st.markdown("**Solo aparecen bloques cuyo horario ya terminó.**")
        slots_pas_recarga = get_slots_con_alumnos_docente(perfil["id"], solo_pasados=True)

        if not slots_pas_recarga:
            st.info("No hay sesiones pasadas pendientes.")
        else:
            for slot in slots_pas_recarga:
                titulo  = fmt_fecha_slot(slot["fecha"], slot["hora_inicio"], slot["hora_fin"])
                mat     = slot.get("materia_nombre", "—")
                alumnos = slot["alumnos"]
                usados  = slot.get("cupos_usados", 0)
                cupos   = slot.get("cupos", 8)

                # Verificar si ya todos tienen asistencia registrada
                todos_reg = all(a.get("asistencia") is not None for a in alumnos) if alumnos else False
                estado_bloque = "✅ Completado" if todos_reg else "⏳ Pendiente"

                with st.expander(f"📆 {titulo}  ·  📖 {mat}  ·  {estado_bloque}  ·  👥 {usados}/{cupos}"):
                    if not alumnos:
                        st.caption("Ningún alumno reservó este bloque.")
                    else:
                        notas = st.text_area(
                            "Notas generales de la sesión",
                            placeholder="Temas tratados, observaciones…",
                            height=60,
                            key=f"notas_{slot['id']}"
                        )
                        cambios = {}
                        for alumno in alumnos:
                            sid    = alumno["id"]
                            nom    = alumno.get("alumno_nombre", "—")
                            ctrl   = alumno.get("alumno_control", "—")
                            ya_reg = alumno.get("asistencia") is not None
                            idx    = 0 if alumno.get("asistencia") is not False else 1

                            col_n, col_r = st.columns([2, 1])
                            with col_n:
                                tag = "<span class='badge-green'>Ya registrado</span>" if ya_reg else ""
                                st.markdown(f"""
                                <div style="padding:6px 0;">
                                    <strong style="color:#0d2137;">{nom}</strong>
                                    <small style="color:#5a7080;"> · {ctrl}</small>
                                    &nbsp;{tag}
                                </div>""", unsafe_allow_html=True)
                            with col_r:
                                asistio = st.radio(
                                    "Asistencia",
                                    ["✅ Asistió", "❌ No asistió"],
                                    key=f"asist_{sid}",
                                    horizontal=True,
                                    index=idx,
                                    label_visibility="collapsed"
                                )
                                cambios[sid] = asistio == "✅ Asistió"

                        if st.button("💾 Guardar asistencias de este bloque",
                                     type="primary", key=f"guardar_{slot['id']}",
                                     use_container_width=True):
                            errores = 0
                            for sesion_id, asistio in cambios.items():
                                if not registrar_asistencia(sesion_id, asistio, notas):
                                    errores += 1
                            if errores == 0:
                                st.success("✅ Asistencias guardadas.")
                                st.rerun()
                            else:
                                st.error(f"{errores} error(es) al guardar.")
