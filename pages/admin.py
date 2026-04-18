"""
pages/admin.py
Panel del Administrador — TutorIA
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from utils.styles import inject_css, estado_badge
from utils.auth import require_auth, get_current_perfil, get_current_rol
from utils.db import get_todas_sesiones, get_todos_usuarios, actualizar_usuario
from components.sidebar import render_sidebar

st.set_page_config(page_title="TutorIA · Admin", page_icon="⚙️", layout="wide")
inject_css()
require_auth()

if get_current_rol() != "administrador":
    st.error("Acceso restringido a administradores.")
    st.stop()

perfil = get_current_perfil()
render_sidebar()


def fmt_fecha(iso_str):
    try:
        return datetime.fromisoformat(iso_str.replace("Z", "+00:00")).strftime("%d/%m/%Y %H:%M")
    except Exception:
        return iso_str or "—"


def safe_to_datetime(series):
    """Convierte una serie de fechas ISO a datetime de forma segura."""
    return pd.to_datetime(series, utc=True, errors="coerce")


# ── Header ───────────────────────────────────────────────
st.markdown("""
<div class="dash-header">
    <div><h2>⚙️ Panel de Administración <span class="role-tag">Administrador</span></h2></div>
</div>
""", unsafe_allow_html=True)

# ── Datos ────────────────────────────────────────────────
sesiones = get_todas_sesiones()
usuarios = get_todos_usuarios()

# ── Métricas ─────────────────────────────────────────────
alumnos_count   = sum(1 for u in usuarios if u["rol"] == "alumno")
docentes_count  = sum(1 for u in usuarios if u["rol"] == "docente")
total_ses       = len(sesiones)
completadas_ses = sum(1 for s in sesiones if s["estado"] == "Completada")
pct_asist       = round((completadas_ses / total_ses * 100) if total_ses else 0, 1)

st.markdown(f"""
<div class="metric-row">
    <div class="metric-box"><div class="num">{alumnos_count}</div><div class="lbl">Alumnos</div></div>
    <div class="metric-box"><div class="num">{docentes_count}</div><div class="lbl">Docentes</div></div>
    <div class="metric-box"><div class="num">{total_ses}</div><div class="lbl">Total sesiones</div></div>
    <div class="metric-box"><div class="num">{completadas_ses}</div><div class="lbl">Completadas</div></div>
    <div class="metric-box"><div class="num">{pct_asist}%</div><div class="lbl">% Asistencia</div></div>
</div>
""", unsafe_allow_html=True)

tab_reportes, tab_usuarios, tab_sesiones = st.tabs(
    ["📊 Reportes", "👥 Usuarios", "📋 Todas las sesiones"]
)

# ── TAB REPORTES ─────────────────────────────────────────
with tab_reportes:
    col_g1, col_g2 = st.columns(2, gap="large")

    with col_g1:
        st.markdown("<div class='tutoria-card'><h3>📊 Sesiones por estado</h3>", unsafe_allow_html=True)
        if sesiones:
            df_estado = (
                pd.DataFrame(sesiones)[["estado"]]
                .value_counts()
                .reset_index()
                .rename(columns={"count": "cantidad"})
            )
            fig = px.pie(df_estado, names="estado", values="cantidad",
                         color_discrete_sequence=["#2c7da0", "#2b7e3a", "#ef4444", "#94a3b8"],
                         hole=0.45)
            fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=280)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sin datos.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_g2:
        st.markdown("<div class='tutoria-card'><h3>📚 Sesiones por docente</h3>", unsafe_allow_html=True)
        if sesiones:
            df_doc = (
                pd.DataFrame(sesiones)[["docente_nombre"]]
                .value_counts()
                .reset_index()
                .rename(columns={"count": "sesiones"})
            )
            fig2 = px.bar(df_doc, x="sesiones", y="docente_nombre",
                          orientation="h",
                          color_discrete_sequence=["#1e3a5f"])
            fig2.update_layout(margin=dict(t=10, b=10, l=10, r=10),
                               yaxis_title="", xaxis_title="Sesiones", height=280)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Sin datos.")
        st.markdown("</div>", unsafe_allow_html=True)

    # Gráfica mensual — usa utc=True para evitar el ValueError de strptime
    st.markdown("<div class='tutoria-card'><h3>📈 Sesiones por mes</h3>", unsafe_allow_html=True)
    if sesiones:
        df_all = pd.DataFrame(sesiones)
        df_all["fecha_dt"] = safe_to_datetime(df_all["fecha_hora"])
        df_all = df_all.dropna(subset=["fecha_dt"])
        if not df_all.empty:
            df_all["mes"] = df_all["fecha_dt"].dt.to_period("M").astype(str)
            df_mes = df_all.groupby("mes").size().reset_index(name="sesiones")
            fig3 = px.line(df_mes, x="mes", y="sesiones", markers=True,
                           color_discrete_sequence=["#2c7da0"])
            fig3.update_layout(margin=dict(t=10, b=10, l=10, r=10),
                               xaxis_title="Mes", yaxis_title="Sesiones", height=250)
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("Sin datos de fechas válidas.")
    else:
        st.info("Sin datos.")
    st.markdown("</div>", unsafe_allow_html=True)

    if sesiones:
        csv = pd.DataFrame(sesiones).to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Exportar reporte CSV",
            data=csv,
            file_name=f"reporte_tutorias_{datetime.today().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )

# ── TAB USUARIOS ─────────────────────────────────────────
with tab_usuarios:
    st.markdown("<div class='tutoria-card'><h3>👥 Gestión de usuarios</h3>", unsafe_allow_html=True)

    filtro_rol = st.selectbox("Filtrar por rol",
                              ["Todos", "alumno", "docente", "administrador"])
    usr_filtrados = (usuarios if filtro_rol == "Todos"
                     else [u for u in usuarios if u["rol"] == filtro_rol])

    if not usr_filtrados:
        st.info("No hay usuarios para mostrar.")
    else:
        filas = ""
        for u in usr_filtrados:
            activo_badge = ('<span class="badge-green">Activo</span>' if u.get("activo")
                            else '<span class="badge-red">Inactivo</span>')
            rol_badge = {
                "alumno":        '<span class="badge-blue">Alumno</span>',
                "docente":       '<span class="badge-gray">Docente</span>',
                "administrador": '<span class="badge-green">Admin</span>',
            }.get(u["rol"], u["rol"])
            extra = u.get("numero_control") or u.get("departamento") or "—"
            filas += f"""
            <tr>
                <td>{u['nombre']} {u['apellido']}</td>
                <td>{u['correo']}</td>
                <td>{rol_badge}</td>
                <td>{extra}</td>
                <td>{activo_badge}</td>
            </tr>"""

        st.markdown(f"""
        <table class="hist-table">
            <thead>
                <tr><th>Nombre</th><th>Correo</th><th>Rol</th><th>Control/Depto</th><th>Estado</th></tr>
            </thead>
            <tbody>{filas}</tbody>
        </table>""", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
    st.divider()

    st.markdown("#### ✏️ Cambiar estado de un usuario")
    otros = [u for u in usuarios if u["id"] != perfil["id"]]
    if otros:
        opciones_usr = {f"{u['nombre']} {u['apellido']} ({u['correo']})": u for u in otros}
        sel_usr  = st.selectbox("Usuario", list(opciones_usr.keys()), key="sel_usr_admin")
        usr_sel  = opciones_usr[sel_usr]
        nuevo_estado = st.toggle("Usuario activo", value=usr_sel.get("activo", True))

        if st.button("Guardar cambio", type="primary"):
            ok = actualizar_usuario(usr_sel["id"], {"activo": nuevo_estado})
            if ok:
                st.success("Estado actualizado.")
                st.rerun()

# ── TAB TODAS LAS SESIONES ────────────────────────────────
with tab_sesiones:
    st.markdown("<div class='tutoria-card'><h3>📋 Registro completo de sesiones</h3>",
                unsafe_allow_html=True)

    c_fil1, c_fil2 = st.columns(2)
    with c_fil1:
        filtro_estado = st.selectbox(
            "Estado", ["Todos", "Programada", "Completada", "Cancelada", "No asistió"],
            key="fil_estado")
    with c_fil2:
        docentes_nombres = ["Todos"] + sorted({s.get("docente_nombre", "") for s in sesiones})
        filtro_doc = st.selectbox("Docente", docentes_nombres, key="fil_doc")

    ses_filtradas = sesiones
    if filtro_estado != "Todos":
        ses_filtradas = [s for s in ses_filtradas if s["estado"] == filtro_estado]
    if filtro_doc != "Todos":
        ses_filtradas = [s for s in ses_filtradas if s.get("docente_nombre") == filtro_doc]

    if not ses_filtradas:
        st.info("No hay sesiones con los filtros seleccionados.")
    else:
        filas = ""
        for s in ses_filtradas:
            fh  = fmt_fecha(s.get("fecha_hora", ""))
            bdg = estado_badge(s["estado"])
            filas += f"""
            <tr>
                <td>{fh}</td>
                <td>{s.get('alumno_nombre','—')}</td>
                <td>{s.get('alumno_control','—')}</td>
                <td>{s.get('docente_nombre','—')}</td>
                <td>{s.get('materia','—')}</td>
                <td>{bdg}</td>
            </tr>"""

        st.markdown(f"""
        <table class="hist-table">
            <thead>
                <tr>
                    <th>Fecha</th><th>Alumno</th><th>Control</th>
                    <th>Docente</th><th>Materia</th><th>Estado</th>
                </tr>
            </thead>
            <tbody>{filas}</tbody>
        </table>""", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
