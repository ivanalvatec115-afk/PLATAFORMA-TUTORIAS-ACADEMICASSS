"""
pages/admin.py — Plataforma de Tutorías Académicas ITMH
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from utils.styles import inject_css, estado_badge
from utils.auth import require_auth, get_current_perfil, get_current_rol
from utils.db import (
    get_todas_sesiones, get_todos_usuarios, actualizar_usuario,
    crear_usuario_completo, eliminar_usuario,
    get_materias, get_materias_docente,
    asignar_materia_docente, quitar_materia_docente,
)
from components.sidebar import render_sidebar

st.set_page_config(page_title="Plataforma de Tutorías Académicas - ITMH · Admin",
                   page_icon="⚙️", layout="wide")
inject_css()
require_auth()

if get_current_rol() != "administrador":
    st.error("Acceso restringido.")
    st.stop()

perfil   = get_current_perfil()
render_sidebar()


def fmt_fecha(iso_str):
    try:
        return datetime.fromisoformat(iso_str.replace("Z", "+00:00")).strftime("%d/%m/%Y %H:%M")
    except Exception:
        return iso_str or "—"


def safe_to_datetime(series):
    return pd.to_datetime(series, utc=True, errors="coerce")


# ── Header ───────────────────────────────────────────────
st.markdown("""
<div class="dash-header">
    <div><h2>⚙️ Panel de Administración <span class="role-tag">Administrador</span></h2></div>
</div>
""", unsafe_allow_html=True)

sesiones = get_todas_sesiones()
usuarios = get_todos_usuarios()

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

tab_usuarios, tab_nuevo, tab_materias, tab_reportes, tab_sesiones = st.tabs([
    "👥 Gestionar usuarios", "➕ Nuevo usuario",
    "📚 Materias por docente", "📊 Reportes", "📋 Todas las sesiones"
])

# ══════════════════════════════════════════════════════════
# TAB: GESTIONAR USUARIOS
# ══════════════════════════════════════════════════════════
with tab_usuarios:
    st.markdown("<div class='tutoria-card'><h3>👥 Editar datos de usuario</h3>", unsafe_allow_html=True)

    filtro_rol = st.selectbox("Filtrar por rol",
                              ["Todos", "alumno", "docente", "administrador"],
                              key="fil_rol_edit")
    usr_filtrados = (usuarios if filtro_rol == "Todos"
                     else [u for u in usuarios if u["rol"] == filtro_rol])

    if not usr_filtrados:
        st.info("No hay usuarios.")
    else:
        opciones_usr = {
            f"{u['nombre']} {u['apellido']} — {u['correo']}": u
            for u in usr_filtrados if u["id"] != perfil["id"]
        }
        if not opciones_usr:
            st.info("No hay otros usuarios en este rol.")
        else:
            sel = st.selectbox("Selecciona usuario a editar",
                               list(opciones_usr.keys()), key="sel_edit")
            u   = opciones_usr[sel]

            with st.form("form_editar_usuario"):
                c1, c2 = st.columns(2)
                with c1:
                    e_nombre   = st.text_input("Nombre(s)",  value=u.get("nombre",""))
                    e_correo   = st.text_input("Correo",     value=u.get("correo",""))
                    e_control  = st.text_input("Nº Control", value=u.get("numero_control","") or "")
                with c2:
                    e_apellido = st.text_input("Apellidos",  value=u.get("apellido",""))
                    e_rol      = st.selectbox("Rol",
                                             ["alumno","docente","administrador"],
                                             index=["alumno","docente","administrador"].index(u.get("rol","alumno")))
                    e_depto    = st.text_input("Departamento", value=u.get("departamento","") or "")
                e_activo   = st.toggle("Usuario activo", value=u.get("activo", True))
                guardar    = st.form_submit_button("💾 Guardar cambios", type="primary",
                                                   use_container_width=True)

            if guardar:
                ok = actualizar_usuario(u["id"], {
                    "nombre":         e_nombre,
                    "apellido":       e_apellido,
                    "correo":         e_correo,
                    "rol":            e_rol,
                    "numero_control": e_control or None,
                    "departamento":   e_depto or None,
                    "activo":         e_activo,
                })
                if ok:
                    st.success("✅ Usuario actualizado.")
                    st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # Tabla de todos los usuarios
    st.markdown("<div class='tutoria-card'><h3>📋 Lista de usuarios</h3>", unsafe_allow_html=True)
    filas = ""
    for u in usuarios:
        activo_b = ('<span class="badge-green">Activo</span>' if u.get("activo")
                    else '<span class="badge-red">Inactivo</span>')
        rol_b = {"alumno": '<span class="badge-blue">Alumno</span>',
                 "docente": '<span class="badge-gray">Docente</span>',
                 "administrador": '<span class="badge-green">Admin</span>'}.get(u["rol"], u["rol"])
        extra = u.get("numero_control") or u.get("departamento") or "—"
        filas += f"""<tr>
            <td>{u['nombre']} {u['apellido']}</td>
            <td>{u['correo']}</td>
            <td>{rol_b}</td>
            <td>{extra}</td>
            <td>{activo_b}</td>
        </tr>"""
    st.markdown(f"""
    <table class="hist-table">
        <thead><tr><th>Nombre</th><th>Correo</th><th>Rol</th><th>Control/Depto</th><th>Estado</th></tr></thead>
        <tbody>{filas}</tbody>
    </table>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# TAB: NUEVO USUARIO
# ══════════════════════════════════════════════════════════
with tab_nuevo:
    st.markdown("<div class='tutoria-card'><h3>➕ Registrar nuevo usuario</h3>", unsafe_allow_html=True)
    st.info("El usuario se creará en Supabase Auth y quedará activo de inmediato.")

    with st.form("form_nuevo_usuario", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            n_nombre  = st.text_input("Nombre(s) *")
            n_correo  = st.text_input("Correo institucional *")
            n_pass    = st.text_input("Contraseña * (mín. 6 caracteres)", type="password")
        with c2:
            n_apellido = st.text_input("Apellidos *")
            n_rol      = st.selectbox("Rol *", ["alumno", "docente", "administrador"])
            n_pass2    = st.text_input("Confirmar contraseña *", type="password")

        n_control = n_depto = None
        if n_rol == "alumno":
            n_control = st.text_input("Número de control")
        else:
            n_depto = st.text_input("Departamento / Área")

        crear = st.form_submit_button("✅ Crear usuario", type="primary",
                                      use_container_width=True)

    if crear:
        if not all([n_nombre, n_apellido, n_correo, n_pass, n_pass2]):
            st.error("Completa todos los campos obligatorios (*).")
        elif n_pass != n_pass2:
            st.error("Las contraseñas no coinciden.")
        elif len(n_pass) < 6:
            st.error("La contraseña debe tener al menos 6 caracteres.")
        else:
            with st.spinner("Creando usuario en Supabase…"):
                ok, resultado = crear_usuario_completo(
                    n_nombre, n_apellido, n_correo, n_pass,
                    n_rol, n_control, n_depto
                )
            if ok:
                st.success(f"✅ Usuario '{n_nombre} {n_apellido}' creado y activado correctamente.")
                st.rerun()
            else:
                st.error(f"Error al crear usuario: {resultado}")

    st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# TAB: MATERIAS POR DOCENTE
# ══════════════════════════════════════════════════════════
with tab_materias:
    st.markdown("<div class='tutoria-card'><h3>📚 Asignar materias a docentes</h3>",
                unsafe_allow_html=True)

    docentes = [u for u in usuarios if u["rol"] == "docente"]
    if not docentes:
        st.info("No hay docentes registrados.")
    else:
        todas_materias = get_materias()
        opciones_doc   = {f"{d['nombre']} {d['apellido']}": d for d in docentes}
        sel_doc_label  = st.selectbox("Selecciona docente", list(opciones_doc.keys()),
                                      key="sel_doc_mat")
        doc_sel        = opciones_doc[sel_doc_label]

        mat_asignadas  = get_materias_docente(doc_sel["id"])
        ids_asignados  = {m["id"] for m in mat_asignadas}

        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("**Materias asignadas:**")
            if not mat_asignadas:
                st.caption("Ninguna asignada.")
            for m in mat_asignadas:
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"<small style='color:#0d2137;'>📖 {m['nombre']}</small>",
                                unsafe_allow_html=True)
                with c2:
                    if st.button("✕", key=f"quitar_{doc_sel['id']}_{m['id']}",
                                 help="Quitar materia"):
                        quitar_materia_docente(doc_sel["id"], m["id"])
                        st.rerun()

        with col_b:
            st.markdown("**Agregar materia:**")
            disponibles = [m for m in todas_materias if m["id"] not in ids_asignados]
            if not disponibles:
                st.caption("Ya tiene todas las materias asignadas.")
            else:
                mat_add = st.selectbox("Materia a agregar",
                                       [m["nombre"] for m in disponibles],
                                       key="mat_add_sel")
                if st.button("➕ Asignar", type="primary", key="btn_asignar_mat"):
                    mat_obj = next(m for m in disponibles if m["nombre"] == mat_add)
                    asignar_materia_docente(doc_sel["id"], mat_obj["id"])
                    st.success(f"Materia '{mat_add}' asignada.")
                    st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# TAB: REPORTES
# ══════════════════════════════════════════════════════════
with tab_reportes:
    col_g1, col_g2 = st.columns(2, gap="large")

    with col_g1:
        st.markdown("<div class='tutoria-card'><h3>📊 Sesiones por estado</h3>",
                    unsafe_allow_html=True)
        if sesiones:
            df_e = pd.DataFrame(sesiones)[["estado"]].value_counts().reset_index().rename(columns={"count":"cantidad"})
            fig  = px.pie(df_e, names="estado", values="cantidad",
                          color_discrete_sequence=["#1a6fa8","#155f2e","#8b1a1a","#7a3a00"],
                          hole=0.45)
            fig.update_layout(margin=dict(t=10,b=10,l=10,r=10), height=280)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sin datos.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_g2:
        st.markdown("<div class='tutoria-card'><h3>📚 Sesiones por docente</h3>",
                    unsafe_allow_html=True)
        if sesiones:
            df_d = pd.DataFrame(sesiones)[["docente_nombre"]].value_counts().reset_index().rename(columns={"count":"sesiones"})
            fig2 = px.bar(df_d, x="sesiones", y="docente_nombre", orientation="h",
                          color_discrete_sequence=["#0d2137"])
            fig2.update_layout(margin=dict(t=10,b=10,l=10,r=10),
                               yaxis_title="", xaxis_title="Sesiones", height=280)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Sin datos.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='tutoria-card'><h3>📈 Sesiones por mes</h3>", unsafe_allow_html=True)
    if sesiones:
        df_all = pd.DataFrame(sesiones)
        df_all["fecha_dt"] = safe_to_datetime(df_all["fecha_hora"])
        df_all = df_all.dropna(subset=["fecha_dt"])
        if not df_all.empty:
            df_all["mes"] = df_all["fecha_dt"].dt.to_period("M").astype(str)
            df_mes = df_all.groupby("mes").size().reset_index(name="sesiones")
            fig3   = px.line(df_mes, x="mes", y="sesiones", markers=True,
                             color_discrete_sequence=["#1a6fa8"])
            fig3.update_layout(margin=dict(t=10,b=10,l=10,r=10), height=250)
            st.plotly_chart(fig3, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if sesiones:
        csv = pd.DataFrame(sesiones).to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Exportar CSV", data=csv,
                           file_name=f"reporte_{datetime.today().strftime('%Y%m%d')}.csv",
                           mime="text/csv")

# ══════════════════════════════════════════════════════════
# TAB: TODAS LAS SESIONES
# ══════════════════════════════════════════════════════════
with tab_sesiones:
    st.markdown("<div class='tutoria-card'><h3>📋 Registro completo</h3>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        f_estado = st.selectbox("Estado",
                                ["Todos","Programada","Completada","Cancelada","No asistió"],
                                key="fil_est")
    with c2:
        doc_names = ["Todos"] + sorted({s.get("docente_nombre","") for s in sesiones})
        f_doc     = st.selectbox("Docente", doc_names, key="fil_doc2")

    filtradas = sesiones
    if f_estado != "Todos":
        filtradas = [s for s in filtradas if s["estado"] == f_estado]
    if f_doc != "Todos":
        filtradas = [s for s in filtradas if s.get("docente_nombre") == f_doc]

    if not filtradas:
        st.info("Sin sesiones con los filtros aplicados.")
    else:
        filas = ""
        for s in filtradas:
            fh  = fmt_fecha(s.get("fecha_hora",""))
            bdg = estado_badge(s["estado"])
            filas += f"""<tr>
                <td>{fh}</td>
                <td>{s.get('alumno_nombre','—')}</td>
                <td>{s.get('alumno_control','—')}</td>
                <td>{s.get('docente_nombre','—')}</td>
                <td>{s.get('materia','—')}</td>
                <td>{bdg}</td>
            </tr>"""
        st.markdown(f"""
        <table class="hist-table">
            <thead><tr>
                <th>Fecha</th><th>Alumno</th><th>Control</th>
                <th>Docente</th><th>Materia</th><th>Estado</th>
            </tr></thead>
            <tbody>{filas}</tbody>
        </table>""", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
