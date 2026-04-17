"""
pages/docente.py
Dashboard del Docente Tutor — TutorIA
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
    registrar_asistencia,
)
from components.sidebar import render_sidebar

st.set_page_config(page_title="TutorIA · Docente", page_icon="📚", layout="wide")
inject_css()
require_auth()

if get_current_rol() != "docente":
    st.error("Acceso restringido.")
    st.stop()

perfil = get_current_perfil()
render_sidebar()

# ── Header ───────────────────────────────────────────────
st.markdown(f"""
<div class="dash-header">
    <div>
        <h2>📚 Panel del Docente <span class="role-tag">Docente Tutor</span></h2>
    </div>
    <div style="color:#5b6e8c; font-size:0.85rem;">
        {perfil['nombre']} {perfil['apellido']} · {perfil.get('departamento','—')}
    </div>
</div>
""", unsafe_allow_html=True)

# ── Métricas ─────────────────────────────────────────────
sesiones = get_sesiones_docente(perfil["id"])

total       = len(sesiones)
programadas = sum(1 for s in sesiones if s["estado"] == "Programada")
completadas = sum(1 for s in sesiones if s["estado"] == "Completada")
no_asistio  = sum(1 for s in sesiones if s["estado"] == "No asistió")

st.markdown(f"""
<div class="metric-row">
    <div class="metric-box">
        <div class="num">{total}</div>
        <div class="lbl">Total sesiones</div>
    </div>
    <div class="metric-box">
        <div class="num">{programadas}</div>
        <div class="lbl">Programadas</div>
    </div>
    <div class="metric-box">
        <div class="num">{completadas}</div>
        <div class="lbl">Completadas</div>
    </div>
    <div class="metric-box">
        <div class="num">{no_asistio}</div>
        <div class="lbl">No asistió</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Columnas ─────────────────────────────────────────────
col_left, col_right = st.columns([1, 1.3], gap="large")

# ── IZQUIERDA: Gestionar disponibilidad ──────────────────
with col_left:
    st.markdown("<div class='tutoria-card'><h3>🕐 Gestionar disponibilidad</h3>", unsafe_allow_html=True)

    with st.form("form_disponibilidad", clear_on_submit=True):
        f_fecha  = st.date_input("Fecha", min_value=date.today())
        c1, c2   = st.columns(2)
        with c1:
            f_inicio = st.time_input("Hora inicio", value=time(9, 0))
        with c2:
            f_fin    = st.time_input("Hora fin", value=time(10, 0))
        submitted = st.form_submit_button("➕ Agregar bloque", type="primary",
                                          use_container_width=True)

    if submitted:
        if f_inicio >= f_fin:
            st.error("La hora de inicio debe ser menor a la de fin.")
        else:
            ok = agregar_disponibilidad(perfil["id"], f_fecha, f_inicio, f_fin)
            if ok:
                st.success("Bloque de disponibilidad registrado.")
                st.rerun()

    # Lista de mis bloques
    st.markdown("<b style='color:#5b6e8c; font-size:0.82rem;'>Mis horarios registrados</b>",
                unsafe_allow_html=True)
    slots = get_disponibilidad_docente(perfil["id"])
    if not slots:
        st.caption("Aún no has registrado disponibilidad.")
    else:
        for s in slots:
            estado_txt = "✅ Libre" if s["disponible"] else "🔒 Ocupado"
            col_info, col_btn = st.columns([3, 1])
            with col_info:
                st.markdown(f"""
                <div class="avail-item">
                    <div>
                        <strong>{s['fecha']}</strong><br>
                        <small>{s['hora_inicio'][:5]} – {s['hora_fin'][:5]} &nbsp; {estado_txt}</small>
                    </div>
                </div>""", unsafe_allow_html=True)
            with col_btn:
                if s["disponible"]:
                    if st.button("🗑", key=f"del_{s['id']}", help="Eliminar bloque"):
                        eliminar_disponibilidad(s["id"])
                        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# ── DERECHA: Sesiones + Registro asistencia ───────────────
with col_right:

    tab_programadas, tab_historial, tab_asistencia = st.tabs(
        ["📅 Programadas", "📋 Historial", "✍️ Registrar asistencia"]
    )

    # ── Tab: sesiones programadas ──
    with tab_programadas:
        progs = [s for s in sesiones if s["estado"] == "Programada"]
        if not progs:
            st.info("No tienes sesiones programadas próximas.")
        else:
            for s in progs:
                alum = s.get("perfiles", {})
                nombre_alum = f"{alum.get('nombre','')} {alum.get('apellido','')}"
                ctrl = alum.get("numero_control", "—")
                fh   = datetime.fromisoformat(s["fecha_hora"].replace("Z","")).strftime("%d/%m/%Y %H:%M")
                st.markdown(f"""
                <div class="avail-item">
                    <div>
                        <strong>{nombre_alum}</strong> <small style="color:#5b6e8c">· {ctrl}</small><br>
                        <small>📆 {fh} · 📖 {s.get('materia','—')}</small><br>
                        <small style="color:#888;">{s.get('descripcion','')}</small>
                    </div>
                    <span class="badge-blue">Programada</span>
                </div>
                """, unsafe_allow_html=True)

    # ── Tab: historial completo ──
    with tab_historial:
        if not sesiones:
            st.info("Sin sesiones registradas.")
        else:
            filas = ""
            for s in sesiones:
                alum = s.get("perfiles", {})
                nombre_alum = f"{alum.get('nombre','')} {alum.get('apellido','')}"
                fh   = datetime.fromisoformat(s["fecha_hora"].replace("Z","")).strftime("%d/%m/%Y %H:%M")
                mat  = s.get("materia") or "—"
                bdg  = estado_badge(s["estado"])
                filas += f"""
                <tr>
                    <td>{fh}</td>
                    <td>{nombre_alum}</td>
                    <td>{mat}</td>
                    <td>{bdg}</td>
                </tr>"""
            st.markdown(f"""
            <table class="hist-table">
                <thead>
                    <tr><th>Fecha</th><th>Alumno</th><th>Materia</th><th>Estado</th></tr>
                </thead>
                <tbody>{filas}</tbody>
            </table>""", unsafe_allow_html=True)

    # ── Tab: registrar asistencia ──
    with tab_asistencia:
        progs_asist = [s for s in sesiones if s["estado"] == "Programada"]
        if not progs_asist:
            st.info("No hay sesiones programadas pendientes de cerrar.")
        else:
            opciones = {}
            for s in progs_asist:
                alum = s.get("perfiles", {})
                nombre_alum = f"{alum.get('nombre','')} {alum.get('apellido','')}"
                fh   = datetime.fromisoformat(s["fecha_hora"].replace("Z","")).strftime("%d/%m/%Y %H:%M")
                label = f"{nombre_alum} · {fh}"
                opciones[label] = s

            sel_label = st.selectbox("Selecciona la sesión", list(opciones.keys()))
            ses       = opciones[sel_label]

            asistio = st.radio("¿El alumno asistió?", ["Sí, asistió", "No asistió"],
                               horizontal=True)
            notas   = st.text_area("Notas de la sesión (opcional)",
                                   placeholder="Observaciones, temas tratados, recomendaciones…",
                                   height=90)

            if st.button("💾 Cerrar y guardar sesión", type="primary", use_container_width=True):
                ok = registrar_asistencia(
                    sesion_id=ses["id"],
                    asistio=(asistio == "Sí, asistió"),
                    notas=notas,
                )
                if ok:
                    st.markdown('<div class="msg-success">✅ Sesión cerrada y guardada en el historial académico.</div>',
                                unsafe_allow_html=True)
                    st.rerun()
