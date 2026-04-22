"""
pages/admin.py — Plataforma de Tutorías Académicas ITMH
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from utils.styles import inject_css, estado_badge
from utils.auth import require_auth, get_current_perfil, get_current_rol
from utils.importacion import (
    leer_excel_alumnos, leer_excel_docentes,
    importar_alumnos, importar_docentes,
    generar_correo_alumno, generar_correo_docente, generar_password,
)
from utils.reportes import (
    reporte_admin_excel, reporte_admin_pdf,
    reporte_alumno_excel, reporte_alumno_pdf,
    reporte_docente_excel, reporte_docente_pdf,
)
from utils.db import (
    CUPOS_MAX,
    get_slots_con_alumnos_docente,
    get_slots_todos_docentes,
    get_todas_sesiones, get_todos_usuarios,
    actualizar_usuario_completo,
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

perfil = get_current_perfil()
render_sidebar()


def fmt_fecha(iso_str):
    try:
        return datetime.fromisoformat(iso_str.replace("Z", "+00:00")).strftime("%d/%m/%Y %H:%M")
    except Exception:
        return iso_str or "—"


def fmt_fecha_slot(fecha, h_ini, h_fin):
    try:
        d = datetime.strptime(fecha, "%Y-%m-%d").strftime("%d/%m/%Y")
        return f"{d}  {str(h_ini)[:5]} – {str(h_fin)[:5]}"
    except Exception:
        return f"{fecha} {h_ini}–{h_fin}"


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

tab_usuarios, tab_nuevo, tab_importar, tab_materias, tab_reportes, tab_sesiones = st.tabs([
    "👥 Gestionar usuarios", "➕ Nuevo usuario", "📤 Importar Excel",
    "📚 Materias por docente", "📊 Reportes", "📋 Todas las sesiones"
])

# Lista de departamentos compartida en todo el admin
DEPTOS_LIST = [
    "Ingeniería en Sistemas Computacionales",
    "Ciencias Básicas",
    "Ingeniería Industrial",
    "Ingeniería Eléctrica",
    "Ingeniería Mecánica",
    "Coordinación Académica",
    "Administración",
    "Otro",
]

# ══════════════════════════════════════════════════════════
# TAB: GESTIONAR USUARIOS
# ══════════════════════════════════════════════════════════
with tab_usuarios:
    st.markdown("<div class='tutoria-card'><h3>👥 Editar datos de usuario</h3>",
                unsafe_allow_html=True)

    filtro_rol    = st.selectbox("Filtrar por rol",
                                 ["Todos","alumno","docente","administrador"],
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
            sel        = st.selectbox("Selecciona usuario", list(opciones_usr.keys()),
                                      key="sel_edit")
            u          = opciones_usr[sel]
            rol_actual = u.get("rol", "alumno")

            # ── Un único formulario con datos + contraseña ──
            with st.form("form_editar_usuario"):
                st.markdown("**📋 Datos del usuario**")
                c1, c2 = st.columns(2)
                with c1:
                    e_nombre  = st.text_input("Nombre(s)",  value=u.get("nombre",""))
                    e_correo  = st.text_input("Correo institucional", value=u.get("correo",""))
                    if rol_actual == "alumno":
                        e_control = st.text_input("Nº Control",
                                                  value=u.get("numero_control","") or "")
                        e_depto   = None
                    else:
                        _depto_val = u.get("departamento","") or DEPTOS_LIST[0]
                        _depto_idx = DEPTOS_LIST.index(_depto_val) if _depto_val in DEPTOS_LIST else 0
                        e_depto   = st.selectbox("Departamento", DEPTOS_LIST,
                                                 index=_depto_idx,
                                                 key="edit_depto_sel")
                        e_control = None
                with c2:
                    e_apellido = st.text_input("Apellidos", value=u.get("apellido",""))
                    e_rol      = st.selectbox(
                        "Rol", ["alumno","docente","administrador"],
                        index=["alumno","docente","administrador"].index(rol_actual)
                    )
                    e_activo   = st.toggle("Usuario activo", value=u.get("activo", True))

                st.divider()
                st.markdown("**🔑 Cambiar contraseña** *(dejar en blanco para no cambiar)*")
                cp1, cp2 = st.columns(2)
                with cp1:
                    e_pass1 = st.text_input("Nueva contraseña", type="password",
                                            key="ep1")
                with cp2:
                    e_pass2 = st.text_input("Confirmar contraseña", type="password",
                                            key="ep2")

                guardar = st.form_submit_button("💾 Guardar todos los cambios",
                                                type="primary", use_container_width=True)

            if guardar:
                # Validar contraseña si se ingresó
                nueva_pass = None
                if e_pass1 or e_pass2:
                    if e_pass1 != e_pass2:
                        st.error("Las contraseñas no coinciden.")
                        st.stop()
                    elif len(e_pass1) < 6:
                        st.error("La contraseña debe tener al menos 6 caracteres.")
                        st.stop()
                    else:
                        nueva_pass = e_pass1

                # Detectar si cambió el correo
                nuevo_correo = e_correo if e_correo != u.get("correo","") else None

                datos_perfil = {
                    "nombre":   e_nombre,
                    "apellido": e_apellido,
                    "correo":   e_correo,
                    "rol":      e_rol,
                    "activo":   e_activo,
                }
                if e_control is not None:
                    datos_perfil["numero_control"] = e_control or None
                if e_depto is not None:
                    datos_perfil["departamento"] = e_depto or None

                ok, msg = actualizar_usuario_completo(
                    u["id"], datos_perfil,
                    nuevo_correo=nuevo_correo,
                    nueva_password=nueva_pass
                )
                if ok:
                    cambios_txt = "✅ Datos actualizados."
                    if nuevo_correo:
                        cambios_txt += " Correo actualizado en Auth."
                    if nueva_pass:
                        cambios_txt += " Contraseña actualizada."
                    st.success(cambios_txt)
                    st.rerun()
                else:
                    st.error(f"Error al guardar: {msg}")

    st.markdown("</div>", unsafe_allow_html=True)

    # Tabla resumen
    st.markdown("<div class='tutoria-card'><h3>📋 Lista de usuarios</h3>",
                unsafe_allow_html=True)
    filas = ""
    for u in usuarios:
        activo_b = ('<span class="badge-green">Activo</span>' if u.get("activo")
                    else '<span class="badge-red">Inactivo</span>')
        rol_b = {
            "alumno":        '<span class="badge-blue">Alumno</span>',
            "docente":       '<span class="badge-gray">Docente</span>',
            "administrador": '<span class="badge-green">Admin</span>',
        }.get(u["rol"], u["rol"])
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
    st.markdown("<div class='tutoria-card'><h3>➕ Registrar nuevo usuario</h3>",
                unsafe_allow_html=True)
    st.info("El usuario se creará en Supabase Auth y quedará activo de inmediato.")

    # ── El rol se define FUERA del form para que los campos
    #    condicionales se actualicen en tiempo real sin bug ──
    n_rol = st.selectbox(
        "Rol del nuevo usuario *",
        ["alumno", "docente", "administrador"],
        key="nuevo_rol_selector"
    )

    st.info("Se enviará un link de activación al correo institucional del usuario. "
            "El usuario definirá su propia contraseña al activar la cuenta.")

    with st.form("form_nuevo_usuario", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            n_nombre   = st.text_input("Nombre(s) *")
            n_apellido = st.text_input("Apellidos *")
        with c2:
            st.markdown(
                "<small style='color:#5a7080;'>El correo se genera automáticamente "
                "según el rol y se muestra antes de confirmar.</small>",
                unsafe_allow_html=True
            )
            # Espacio visual
            st.markdown("<br>", unsafe_allow_html=True)

        st.divider()

        if n_rol == "alumno":
            n_control = st.text_input("Número de control *",
                                      key="campo_control_alumno")
            n_depto   = None
        elif n_rol == "docente":
            n_depto   = st.selectbox("Departamento *", DEPTOS_LIST,
                                     key="campo_depto_docente")
            n_control = None
        else:
            n_depto   = st.selectbox("Departamento *", DEPTOS_LIST,
                                     key="campo_depto_admin")
            n_control = None

        crear = st.form_submit_button("📧 Enviar invitación", type="primary",
                                      use_container_width=True)

    # Variable dummy para compatibilidad con el flujo
    n_pass = n_pass2 = ""

    if crear:
        # Generar correo según rol y formato institucional real
        if n_rol == "alumno":
            correo_generado = generar_correo_alumno(n_control or "")
            if not n_control:
                st.error("El número de control es obligatorio para generar el correo del alumno.")
                st.stop()
        else:
            correo_generado = generar_correo_docente(n_nombre, n_apellido)

        if not all([n_nombre, n_apellido]):
            st.error("Completa nombre y apellidos.")
        elif n_rol == "alumno" and not n_control:
            st.error("El número de control es obligatorio para alumnos.")
        elif n_rol in ["docente","administrador"] and not n_depto:
            st.error("El departamento es obligatorio.")
        else:
            st.info(f"📧 Correo que recibirá la invitación: **{correo_generado}**")
            with st.spinner("Enviando invitación…"):
                ok, resultado = crear_usuario_completo(
                    n_nombre.strip(), n_apellido.strip(),
                    correo_generado, "",
                    n_rol, n_control, n_depto
                )
            if ok:
                st.success(
                    f"✅ Invitación enviada a **{correo_generado}**. "
                    f"El usuario recibirá un link para activar su cuenta y definir su contraseña."
                )
                st.rerun()
            else:
                st.error(f"Error: {resultado}")

    st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# TAB: IMPORTAR EXCEL
# ══════════════════════════════════════════════════════════
with tab_importar:
    st.markdown("<div class='tutoria-card'><h3>📤 Importación masiva desde Excel</h3>",
                unsafe_allow_html=True)

    # Descargar plantilla — ruta relativa al repo
    import pathlib
    _plantilla_path = pathlib.Path(__file__).parent.parent / "plantilla_importacion.xlsx"
    with open(_plantilla_path, "rb") as pf:
        plantilla_bytes = pf.read()
    st.download_button(
        "⬇️ Descargar plantilla Excel",
        data=plantilla_bytes,
        file_name="plantilla_importacion_ITMH.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=False,
    )
    st.caption("Descarga la plantilla, llena los datos y súbela aquí. "
               "No modifiques los encabezados ni el nombre de las hojas.")
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Importar Alumnos ──
    st.markdown("<div class='tutoria-card'><h3>🎓 Importar Alumnos</h3>",
                unsafe_allow_html=True)
    archivo_alumnos = st.file_uploader(
        "Sube el Excel con alumnos (hoja: Alumnos)",
        type=["xlsx"],
        key="upload_alumnos"
    )

    if archivo_alumnos:
        bytes_a = archivo_alumnos.read()
        filas_a, errores_a = leer_excel_alumnos(bytes_a)

        if errores_a:
            st.error(f"Se encontraron {len(errores_a)} error(es) de validación:")
            for err in errores_a:
                st.markdown(f"- {err}")
        
        if filas_a:
            st.success(f"✅ {len(filas_a)} alumno(s) listos para importar.")
            # Vista previa
            with st.expander("👁 Vista previa de datos a importar"):
                preview_data = [{
                    "Nombre": f["nombre"],
                    "Apellido": f["apellido"],
                    "No. Control": f["numero_control"],
                    "Correo generado": f["correo"],
                } for f in filas_a]
                st.dataframe(preview_data, use_container_width=True)

            if st.button("✅ Confirmar importación de alumnos", type="primary",
                         use_container_width=True, key="btn_imp_alumnos"):
                with st.spinner("Creando usuarios en Supabase…"):
                    ok_a, fail_a, errs_imp_a = importar_alumnos(filas_a)
                st.success(f"✅ {ok_a} alumno(s) creados correctamente.")
                if fail_a:
                    st.error(f"❌ {fail_a} alumno(s) con error:")
                    for e in errs_imp_a:
                        st.markdown(f"- {e}")
                if ok_a > 0:
                    st.rerun()
        elif not errores_a:
            st.warning("El archivo no contiene filas con datos. Verifica que llenaste la hoja 'Alumnos'.")

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Importar Docentes ──
    st.markdown("<div class='tutoria-card'><h3>📚 Importar Docentes</h3>",
                unsafe_allow_html=True)
    archivo_docentes = st.file_uploader(
        "Sube el Excel con docentes (hoja: Docentes)",
        type=["xlsx"],
        key="upload_docentes"
    )

    if archivo_docentes:
        bytes_d = archivo_docentes.read()
        filas_d, errores_d = leer_excel_docentes(bytes_d)

        if errores_d:
            st.error(f"Se encontraron {len(errores_d)} error(es) de validación:")
            for err in errores_d:
                st.markdown(f"- {err}")

        if filas_d:
            st.success(f"✅ {len(filas_d)} docente(s) listos para importar.")
            with st.expander("👁 Vista previa de datos a importar"):
                preview_d = [{
                    "Nombre": f["nombre"],
                    "Apellido": f["apellido"],
                    "Departamento": f["departamento"],
                    "Correo generado": f["correo"],
                } for f in filas_d]
                st.dataframe(preview_d, use_container_width=True)

            if st.button("✅ Confirmar importación de docentes", type="primary",
                         use_container_width=True, key="btn_imp_docentes"):
                with st.spinner("Creando usuarios en Supabase…"):
                    ok_d, fail_d, errs_imp_d = importar_docentes(filas_d)
                st.success(f"✅ {ok_d} docente(s) creados correctamente.")
                if fail_d:
                    st.error(f"❌ {fail_d} docente(s) con error:")
                    for e in errs_imp_d:
                        st.markdown(f"- {e}")
                if ok_d > 0:
                    st.rerun()
        elif not errores_d:
            st.warning("El archivo no contiene filas con datos. Verifica que llenaste la hoja 'Docentes'.")

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
                cm1, cm2 = st.columns([3, 1])
                with cm1:
                    st.markdown(f"<small style='color:#0d2137;'>📖 {m['nombre']}</small>",
                                unsafe_allow_html=True)
                with cm2:
                    if st.button("✕", key=f"quitar_{doc_sel['id']}_{m['id']}"):
                        quitar_materia_docente(doc_sel["id"], m["id"])
                        st.rerun()

        with col_b:
            st.markdown("**Agregar materia:**")
            disponibles = [m for m in todas_materias if m["id"] not in ids_asignados]
            if not disponibles:
                st.caption("Ya tiene todas las materias.")
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
            df_e = (pd.DataFrame(sesiones)[["estado"]].value_counts()
                    .reset_index().rename(columns={"count": "cantidad"}))
            fig = px.pie(df_e, names="estado", values="cantidad",
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
            df_d = (pd.DataFrame(sesiones)[["docente_nombre"]].value_counts()
                    .reset_index().rename(columns={"count": "sesiones"}))
            fig2 = px.bar(df_d, x="sesiones", y="docente_nombre", orientation="h",
                          color_discrete_sequence=["#0d2137"])
            fig2.update_layout(margin=dict(t=10,b=10,l=10,r=10),
                               yaxis_title="", xaxis_title="Sesiones", height=280)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Sin datos.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='tutoria-card'><h3>📈 Sesiones por mes</h3>",
                unsafe_allow_html=True)
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

    # ── Descargas ──
    if sesiones:
        st.markdown("<div class='tutoria-card'><h3>📥 Descargar reporte global</h3>",
                    unsafe_allow_html=True)
        col_xl, col_pdf, col_csv = st.columns(3)
        with col_xl:
            try:
                datos, fname = reporte_admin_excel(sesiones, "General")
                st.download_button("⬇️ Excel completo", data=datos,
                                   file_name=fname,
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   use_container_width=True)
            except Exception as e:
                st.error(f"Error Excel: {e}")
        with col_pdf:
            try:
                datos, fname = reporte_admin_pdf(sesiones, "General")
                st.download_button("⬇️ PDF completo", data=datos,
                                   file_name=fname, mime="application/pdf",
                                   use_container_width=True)
            except Exception as e:
                st.error(f"Error PDF: {e}")
        with col_csv:
            csv = pd.DataFrame(sesiones).to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ CSV", data=csv,
                               file_name=f"reporte_{datetime.today().strftime('%Y%m%d')}.csv",
                               mime="text/csv", use_container_width=True)

        st.divider()
        st.markdown("**📋 Reporte por usuario específico**")
        from utils.db import get_sesiones_alumno as _get_sa, get_sesiones_docente as _get_sd
        tipo_rep  = st.selectbox("Tipo de usuario", ["alumno","docente"], key="rep_tipo")
        usrs_rep  = [u for u in usuarios if u["rol"] == tipo_rep]
        if usrs_rep:
            opts_rep  = {f"{u['nombre']} {u['apellido']} ({u['correo']})": u for u in usrs_rep}
            sel_rep   = st.selectbox("Selecciona usuario", list(opts_rep.keys()), key="rep_usr")
            usr_rep   = opts_rep[sel_rep]
            nombre_rep = f"{usr_rep['nombre']} {usr_rep['apellido']}"
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                if st.button("⬇️ Excel del usuario", use_container_width=True, key="btn_rep_xl"):
                    try:
                        if tipo_rep == "alumno":
                            ses_r = _get_sa(usr_rep["id"])
                            datos, fname = reporte_alumno_excel(ses_r, nombre_rep)
                        else:
                            ses_r = _get_sd(usr_rep["id"])
                            datos, fname = reporte_docente_excel(ses_r, nombre_rep)
                        st.download_button("📥 Descargar Excel", data=datos,
                                           file_name=fname,
                                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                           key="dl_rep_xl")
                    except Exception as e:
                        st.error(f"Error: {e}")
            with col_r2:
                if st.button("⬇️ PDF del usuario", use_container_width=True, key="btn_rep_pdf"):
                    try:
                        if tipo_rep == "alumno":
                            ses_r = _get_sa(usr_rep["id"])
                            datos, fname = reporte_alumno_pdf(ses_r, nombre_rep)
                        else:
                            ses_r = _get_sd(usr_rep["id"])
                            datos, fname = reporte_docente_pdf(ses_r, nombre_rep)
                        st.download_button("📥 Descargar PDF", data=datos,
                                           file_name=fname, mime="application/pdf",
                                           key="dl_rep_pdf")
                    except Exception as e:
                        st.error(f"Error: {e}")

        st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# TAB: TODAS LAS SESIONES — agrupadas por bloque (igual que docente)
# ══════════════════════════════════════════════════════════
with tab_sesiones:
    st.markdown("<div class='tutoria-card'><h3>📋 Todas las sesiones por bloque</h3>",
                unsafe_allow_html=True)

    # Filtros
    doc_names  = ["Todos"] + sorted({s.get("docente_nombre","") for s in sesiones if s.get("docente_nombre")})
    mat_names  = ["Todas"] + sorted({s.get("materia","") for s in sesiones if s.get("materia")})
    cf1, cf2, cf3 = st.columns(3)
    with cf1:
        f_doc = st.selectbox("Docente", doc_names, key="fil_doc_slot")
    with cf2:
        f_mat = st.selectbox("Materia", mat_names, key="fil_mat_slot")
    with cf3:
        f_solo = st.selectbox("Período", ["Todos", "Solo pasados", "Solo futuros"],
                              key="fil_periodo")

    st.markdown("</div>", unsafe_allow_html=True)

    # Cargar slots agrupados
    slots_admin = get_slots_todos_docentes()

    # Aplicar filtros
    ahora = datetime.now()
    if f_doc != "Todos":
        slots_admin = [s for s in slots_admin if s.get("docente_nombre") == f_doc]
    if f_mat != "Todas":
        slots_admin = [s for s in slots_admin if s.get("materia_nombre") == f_mat]
    if f_solo == "Solo pasados":
        slots_admin = [s for s in slots_admin
                       if datetime.strptime(f"{s['fecha']} {str(s['hora_fin'])[:5]}", "%Y-%m-%d %H:%M") < ahora]
    elif f_solo == "Solo futuros":
        slots_admin = [s for s in slots_admin
                       if datetime.strptime(f"{s['fecha']} {str(s['hora_fin'])[:5]}", "%Y-%m-%d %H:%M") >= ahora]

    if not slots_admin:
        st.info("No hay bloques con los filtros seleccionados.")
    else:
        for slot in slots_admin:
            titulo  = fmt_fecha_slot(slot["fecha"], slot["hora_inicio"], slot["hora_fin"])
            mat     = slot.get("materia_nombre", "—")
            doc     = slot.get("docente_nombre", "—")
            alumnos = slot.get("alumnos", [])
            usados  = len(alumnos)   # contador real desde sesiones activas
            cupos   = CUPOS_MAX

            # Estado del bloque
            try:
                fin_dt = datetime.strptime(
                    f"{slot['fecha']} {str(slot['hora_fin'])[:5]}", "%Y-%m-%d %H:%M"
                )
                pasado = fin_dt < ahora
            except Exception:
                pasado = False

            todos_reg = all(a.get("asistencia") is not None for a in alumnos) if alumnos else False
            if pasado and alumnos:
                estado_bloque = "✅ Completado" if todos_reg else "⏳ Pendiente asistencia"
            elif not alumnos:
                estado_bloque = "⬜ Sin reservas"
            else:
                estado_bloque = "🔵 Próximo"

            with st.expander(
                f"📆 {titulo}  ·  📖 {mat}  ·  👤 {doc}  ·  {estado_bloque}  ·  👥 {usados}/{cupos}"
            ):
                if not alumnos:
                    st.caption("Ningún alumno ha reservado este bloque.")
                else:
                    filas = ""
                    for a in alumnos:
                        bdg = estado_badge(a.get("estado", "Programada"))
                        asist = "✅" if a.get("asistencia") is True else ("❌" if a.get("asistencia") is False else "—")
                        filas += f"""<tr>
                            <td>{a.get('alumno_nombre','—')}</td>
                            <td>{a.get('alumno_control','—')}</td>
                            <td>{bdg}</td>
                            <td style="text-align:center;">{asist}</td>
                        </tr>"""
                    st.markdown(f"""
                    <table class="hist-table">
                        <thead><tr>
                            <th>Alumno</th><th>No. Control</th>
                            <th>Estado</th><th style="text-align:center;">Asistencia</th>
                        </tr></thead>
                        <tbody>{filas}</tbody>
                    </table>""", unsafe_allow_html=True)
