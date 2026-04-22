"""
utils/db.py — Plataforma de Tutorías Académicas ITMH
"""
from __future__ import annotations
import streamlit as st
from utils.supabase_client import get_supabase, get_supabase_admin
from datetime import date, time, datetime


# ─────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────

def _get_nombre(user_id: str) -> dict:
    if not user_id:
        return {}
    sb = get_supabase()
    try:
        res = (sb.table("perfiles")
                 .select("nombre, apellido, numero_control")
                 .eq("id", user_id).single().execute())
        return res.data or {}
    except Exception as e:
        st.warning(f"⚠️ No se pudo leer perfil: {e}")
        return {}


def _enriquecer_sesiones_alumno(sesiones: list[dict]) -> list[dict]:
    cache = {}
    for s in sesiones:
        did = s.get("docente_id", "")
        if did not in cache:
            cache[did] = _get_nombre(did)
        info = cache[did]
        s["docente_nombre"] = f"{info.get('nombre','')} {info.get('apellido','')}".strip() or f"[{did[:8]}]"
    return sesiones


def _enriquecer_sesiones_docente(sesiones: list[dict]) -> list[dict]:
    cache = {}
    for s in sesiones:
        aid = s.get("alumno_id", "")
        if aid not in cache:
            cache[aid] = _get_nombre(aid)
        info = cache[aid]
        s["alumno_nombre"]  = f"{info.get('nombre','')} {info.get('apellido','')}".strip() or f"[{aid[:8]}]"
        s["alumno_control"] = info.get("numero_control") or "—"
    return sesiones


# ─────────────────────────────────────────────────────────
# MATERIAS
# ─────────────────────────────────────────────────────────

def get_materias() -> list[dict]:
    sb = get_supabase()
    try:
        res = sb.table("materias").select("id, nombre").eq("activa", True).order("nombre").execute()
        return res.data or []
    except Exception as e:
        st.error(f"Error al obtener materias: {e}")
        return []


def get_materias_docente(docente_id: str) -> list[dict]:
    sb = get_supabase()
    try:
        res = (sb.table("docente_materias")
                 .select("materia_id, materias(id, nombre)")
                 .eq("docente_id", docente_id).execute())
        materias = []
        for row in (res.data or []):
            m = row.get("materias", {})
            if isinstance(m, list): m = m[0] if m else {}
            if m: materias.append(m)
        return sorted(materias, key=lambda x: x.get("nombre", ""))
    except Exception as e:
        st.error(f"Error al obtener materias del docente: {e}")
        return []


def asignar_materia_docente(docente_id: str, materia_id: str) -> bool:
    sb = get_supabase()
    try:
        sb.table("docente_materias").insert({"docente_id": docente_id, "materia_id": materia_id}).execute()
        return True
    except Exception as e:
        st.error(f"Error al asignar materia: {e}")
        return False


def quitar_materia_docente(docente_id: str, materia_id: str) -> bool:
    sb = get_supabase()
    try:
        sb.table("docente_materias").delete().eq("docente_id", docente_id).eq("materia_id", materia_id).execute()
        return True
    except Exception as e:
        st.error(f"Error al quitar materia: {e}")
        return False


# ─────────────────────────────────────────────────────────
# DISPONIBILIDAD
# ─────────────────────────────────────────────────────────

def agregar_disponibilidad(docente_id: str, fecha: date,
                           hora_inicio: time, hora_fin: time,
                           materia_id: str, cupos: int = 8) -> bool:
    sb = get_supabase()
    try:
        sb.table("disponibilidad_docentes").insert({
            "docente_id":   docente_id,
            "fecha":        fecha.isoformat(),
            "hora_inicio":  hora_inicio.strftime("%H:%M"),
            "hora_fin":     hora_fin.strftime("%H:%M"),
            "materia_id":   materia_id,
            "cupos":        cupos,
            "cupos_usados": 0,
            "disponible":   True,
        }).execute()
        return True
    except Exception as e:
        st.error(f"Error al agregar disponibilidad: {e}")
        return False


def eliminar_disponibilidad(slot_id: str) -> bool:
    sb = get_supabase()
    try:
        sb.table("disponibilidad_docentes").delete().eq("id", slot_id).execute()
        return True
    except Exception as e:
        st.error(f"Error al eliminar slot: {e}")
        return False


def get_disponibilidad_docente(docente_id: str) -> list[dict]:
    sb = get_supabase()
    try:
        res = (sb.table("disponibilidad_docentes")
                 .select("*, materias(nombre)")
                 .eq("docente_id", docente_id)
                 .order("fecha").order("hora_inicio").execute())
        slots = res.data or []
        for s in slots:
            m = s.get("materias", {})
            if isinstance(m, list): m = m[0] if m else {}
            s["materia_nombre"] = m.get("nombre", "—") if m else "—"
            # Normalizar horas a HH:MM
            s["hora_inicio"] = str(s.get("hora_inicio", ""))[:5]
            s["hora_fin"]    = str(s.get("hora_fin", ""))[:5]
        return slots
    except Exception as e:
        st.error(f"Error al obtener disponibilidad: {e}")
        return []


def get_disponibilidad_por_materia(materia_id: str) -> list[dict]:
    sb = get_supabase()
    try:
        res = (sb.table("disponibilidad_docentes")
                 .select("*")
                 .eq("materia_id", materia_id)
                 .gte("fecha", date.today().isoformat())
                 .order("fecha").order("hora_inicio").execute())
        slots = res.data or []
        resultado = []
        cache = {}
        for s in slots:
            # Recontar cupos desde sesiones reales
            reservas = (sb.table("sesiones_tutoria")
                          .select("id")
                          .eq("disponibilidad_id", s["id"])
                          .neq("estado", "Cancelada")
                          .execute())
            usados = len(reservas.data or [])
            libres = CUPOS_MAX - usados
            if libres <= 0:
                continue  # sin cupos, no mostrar

            did = s.get("docente_id", "")
            if did not in cache:
                cache[did] = _get_nombre(did)
            info = cache[did]
            s["docente_nombre"] = f"{info.get('nombre','')} {info.get('apellido','')}".strip() or "Docente"
            s["cupos_usados"]   = usados
            s["cupos"]          = CUPOS_MAX
            s["cupos_libres"]   = libres
            s["hora_inicio"]    = str(s.get("hora_inicio",""))[:5]
            s["hora_fin"]       = str(s.get("hora_fin",""))[:5]
            resultado.append(s)
        return resultado
    except Exception as e:
        st.error(f"Error al obtener disponibilidad por materia: {e}")
        return []


# ─────────────────────────────────────────────────────────
# SESIONES
# ─────────────────────────────────────────────────────────

def alumno_ya_reservo(alumno_id: str, disponibilidad_id: str) -> bool:
    """Verifica si el alumno ya tiene una reserva activa en ese slot."""
    sb = get_supabase()
    try:
        res = (sb.table("sesiones_tutoria")
                 .select("id")
                 .eq("alumno_id", alumno_id)
                 .eq("disponibilidad_id", disponibilidad_id)
                 .neq("estado", "Cancelada")
                 .execute())
        return len(res.data or []) > 0
    except Exception:
        return False


CUPOS_MAX = 8  # Máximo fijo de alumnos por bloque

def agendar_sesion(alumno_id: str, docente_id: str,
                   disponibilidad_id: str, fecha_hora: str,
                   materia: str, descripcion: str) -> bool:
    """
    Llama a la función SQL agendar_sesion_segura que usa FOR UPDATE
    para evitar condiciones de carrera y garantizar el límite de cupos.
    """
    sb = get_supabase_admin()
    try:
        res = sb.rpc("agendar_sesion_segura", {
            "p_alumno_id":          alumno_id,
            "p_docente_id":         docente_id,
            "p_disponibilidad_id":  disponibilidad_id,
            "p_fecha_hora":         fecha_hora,
            "p_materia":            materia,
            "p_descripcion":        descripcion,
            "p_cupos_max":          CUPOS_MAX,
        }).execute()

        resultado = res.data
        if isinstance(resultado, list):
            resultado = resultado[0] if resultado else {}

        if resultado.get("ok"):
            return True
        else:
            st.error(resultado.get("error", "No se pudo agendar la sesión."))
            return False
    except Exception as e:
        st.error(f"Error al agendar sesión: {e}")
        return False


def cancelar_sesion(sesion_id: str, disponibilidad_id: str | None) -> bool:
    """Cancela UNA sesión de alumno. Usa service_role para evitar RLS."""
    # Usamos admin client para saltarnos RLS en el UPDATE
    sb       = get_supabase()
    sb_admin = get_supabase_admin()
    try:
        # 1. Cancelar la sesión (admin evita bloqueo RLS)
        res = sb_admin.table("sesiones_tutoria")                      .update({"estado": "Cancelada"})                      .eq("id", sesion_id).execute()

        if not res.data:
            st.error("No se pudo cancelar la sesión. Verifica que el ID sea correcto.")
            return False

        # 2. Recalcular cupos reales en el slot
        if disponibilidad_id:
            reservas = sb.table("sesiones_tutoria")                         .select("id")                         .eq("disponibilidad_id", disponibilidad_id)                         .neq("estado", "Cancelada")                         .execute()
            nuevo_usado = len(reservas.data or [])
            sb_admin.table("disponibilidad_docentes").update({
                "cupos_usados": nuevo_usado,
                "cupos":        CUPOS_MAX,
                "disponible":   nuevo_usado < CUPOS_MAX,
            }).eq("id", disponibilidad_id).execute()

        return True
    except Exception as e:
        st.error(f"Error al cancelar sesión: {e}")
        return False


def cancelar_slot_docente(disponibilidad_id: str) -> bool:
    """
    Cancela un bloque completo del docente:
    1. Marca todas las sesiones como Cancelada (quedan en historial de alumnos)
    2. ELIMINA el slot de disponibilidad para que no se pueda reservar más
    """
    sb = get_supabase()
    try:
        # 1. Marcar todas las sesiones activas como Cancelada (persisten en historial)
        sb.table("sesiones_tutoria").update({"estado": "Cancelada"})          .eq("disponibilidad_id", disponibilidad_id)          .neq("estado", "Cancelada").execute()
        # 2. Eliminar el slot de disponibilidad por completo
        sb.table("disponibilidad_docentes").delete()          .eq("id", disponibilidad_id).execute()
        return True
    except Exception as e:
        st.error(f"Error al cancelar bloque: {e}")
        return False


def get_sesiones_alumno(alumno_id: str) -> list[dict]:
    # Usa admin para evitar RLS que pudiera filtrar filas actualizadas por docente
    sb_admin = get_supabase_admin()
    try:
        res = (sb_admin.table("sesiones_tutoria")
                 .select("id, alumno_id, docente_id, disponibilidad_id, fecha_hora, "
                         "materia, descripcion, estado, asistencia, notas_docente, created_at")
                 .eq("alumno_id", alumno_id)
                 .order("fecha_hora", desc=True).execute())
        return _enriquecer_sesiones_alumno(res.data or [])
    except Exception as e:
        st.error(f"Error al obtener sesiones: {e}")
        return []


def get_sesiones_docente(docente_id: str) -> list[dict]:
    sb_admin = get_supabase_admin()
    try:
        res = (sb_admin.table("sesiones_tutoria")
                 .select("id, alumno_id, docente_id, disponibilidad_id, fecha_hora, "
                         "materia, descripcion, estado, asistencia, notas_docente, created_at")
                 .eq("docente_id", docente_id)
                 .order("fecha_hora", desc=True).execute())
        return _enriquecer_sesiones_docente(res.data or [])
    except Exception as e:
        st.error(f"Error al obtener sesiones: {e}")
        return []


def get_slots_con_alumnos_docente(docente_id: str, solo_pasados: bool = False) -> list[dict]:
    """
    Retorna los slots del docente agrupados, cada uno con su lista de alumnos.
    solo_pasados=True → solo slots cuya hora_fin ya pasó (para asistencia).
    solo_pasados=False → solo slots futuros o en curso (para programadas).
    """
    sb = get_supabase()
    try:
        res = (sb.table("disponibilidad_docentes")
                 .select("*, materias(nombre)")
                 .eq("docente_id", docente_id)
                 .order("fecha", desc=solo_pasados)
                 .order("hora_inicio", desc=solo_pasados)
                 .execute())
        todos = res.data or []
        ahora = datetime.now()
        resultado = []
        for s in todos:
            try:
                # Supabase puede devolver "HH:MM:SS" o "HH:MM", normalizamos
                hora_fin_str = str(s['hora_fin'])[:5]
                hora_ini_str = str(s['hora_inicio'])[:5]
                hora_fin_dt  = datetime.strptime(f"{s['fecha']} {hora_fin_str}", "%Y-%m-%d %H:%M")
            except Exception:
                continue

            if solo_pasados and hora_fin_dt >= ahora:
                continue
            if not solo_pasados and hora_fin_dt < ahora:
                continue

            m = s.get("materias", {})
            if isinstance(m, list): m = m[0] if m else {}
            s["materia_nombre"] = m.get("nombre", "—") if m else "—"
            s["hora_inicio"]    = str(s.get("hora_inicio",""))[:5]
            s["hora_fin"]       = str(s.get("hora_fin",""))[:5]

            # Cargar alumnos de este slot (fuente de verdad para el contador)
            ses_res = (sb.table("sesiones_tutoria")
                         .select("id, alumno_id, estado, asistencia, notas_docente, materia")
                         .eq("disponibilidad_id", s["id"])
                         .neq("estado", "Cancelada")
                         .execute())
            alumnos = []
            for ses in (ses_res.data or []):
                info = _get_nombre(ses.get("alumno_id", ""))
                ses["alumno_nombre"]  = f"{info.get('nombre','')} {info.get('apellido','')}".strip() or "—"
                ses["alumno_control"] = info.get("numero_control") or "—"
                alumnos.append(ses)

            # Contador real desde sesiones activas
            s["cupos_usados"] = len(alumnos)
            s["cupos"]        = CUPOS_MAX
            s["cupos_libres"] = CUPOS_MAX - len(alumnos)
            s["alumnos"]      = alumnos
            if alumnos or not solo_pasados:
                resultado.append(s)

        return resultado
    except Exception as e:
        st.error(f"Error al obtener slots: {e}")
        return []


def get_alumnos_por_slot(disponibilidad_id: str) -> list[dict]:
    sb = get_supabase()
    try:
        res = (sb.table("sesiones_tutoria")
                 .select("id, alumno_id, estado, asistencia, notas_docente")
                 .eq("disponibilidad_id", disponibilidad_id)
                 .neq("estado", "Cancelada").execute())
        sesiones = res.data or []
        for s in sesiones:
            info = _get_nombre(s.get("alumno_id", ""))
            s["alumno_nombre"]  = f"{info.get('nombre','')} {info.get('apellido','')}".strip() or "—"
            s["alumno_control"] = info.get("numero_control") or "—"
        return sesiones
    except Exception as e:
        st.error(f"Error al obtener alumnos del slot: {e}")
        return []


def registrar_asistencia(sesion_id: str, asistio: bool, notas: str = "") -> bool:
    """Usa service_role para evitar bloqueo RLS al actualizar estado."""
    sb_admin = get_supabase_admin()
    try:
        res = sb_admin.table("sesiones_tutoria").update({
            "asistencia":    asistio,
            "estado":        "Completada" if asistio else "No asistió",
            "notas_docente": notas,
        }).eq("id", sesion_id).execute()

        if not res.data:
            st.error("No se pudo guardar la asistencia. Verifica que la sesión exista.")
            return False
        return True
    except Exception as e:
        st.error(f"Error al registrar asistencia: {e}")
        return False


# ─────────────────────────────────────────────────────────
# ADMIN
# ─────────────────────────────────────────────────────────

def get_todas_sesiones() -> list[dict]:
    sb = get_supabase()
    try:
        res = sb.table("vista_sesiones").select("*").order("fecha_hora", desc=True).execute()
        return res.data or []
    except Exception as e:
        st.error(f"Error al obtener sesiones: {e}")
        return []


def get_todos_usuarios() -> list[dict]:
    sb = get_supabase()
    try:
        res = sb.table("perfiles").select("*").order("rol").order("apellido").execute()
        return res.data or []
    except Exception as e:
        st.error(f"Error al obtener usuarios: {e}")
        return []


def actualizar_usuario(user_id: str, datos: dict) -> bool:
    sb = get_supabase()
    try:
        sb.table("perfiles").update(datos).eq("id", user_id).execute()
        return True
    except Exception as e:
        st.error(f"Error al actualizar usuario: {e}")
        return False


APP_URL = "https://plataforma-tutorias-academicasss-jze9ktp9wvmmegae8tpv2i.streamlit.app"

def crear_usuario_completo(nombre: str, apellido: str, correo: str,
                           password: str, rol: str,
                           numero_control: str = None,
                           departamento: str = None) -> tuple[bool, str]:
    """
    Invita al usuario por email. Supabase envía un link que redirige
    a la página /activar de la app donde el usuario crea su contraseña.
    El parámetro password se ignora — el usuario define la suya al activar.
    """
    sb_admin = get_supabase_admin()
    try:
        res = sb_admin.auth.admin.invite_user_by_email(
            correo,
            options={
                "redirect_to": f"{APP_URL}/activar",
                "data": {
                    "nombre":   nombre,
                    "apellido": apellido,
                    "rol":      rol,
                }
            }
        )
        if res.user:
            sb_admin.table("perfiles").upsert({
                "id":             res.user.id,
                "nombre":         nombre,
                "apellido":       apellido,
                "correo":         correo,
                "rol":            rol,
                "numero_control": numero_control or None,
                "departamento":   departamento or None,
                "activo":         True,
            }).execute()
            return True, res.user.id
        return False, "No se pudo enviar la invitación."
    except Exception as e:
        return False, str(e)


def cambiar_password_usuario(user_id: str, nueva_password: str) -> tuple[bool, str]:
    """Cambia la contraseña de un usuario usando service_role."""
    sb_admin = get_supabase_admin()
    try:
        sb_admin.auth.admin.update_user_by_id(user_id, {"password": nueva_password})
        return True, "Contraseña actualizada."
    except Exception as e:
        return False, str(e)




def actualizar_usuario_completo(user_id: str, datos_perfil: dict,
                                 nuevo_correo: str = None,
                                 nueva_password: str = None) -> tuple[bool, str]:
    """Actualiza perfil en tabla perfiles Y en Supabase Auth si cambia correo/password."""
    sb       = get_supabase()
    sb_admin = get_supabase_admin()
    try:
        # 1. Actualizar tabla perfiles
        sb.table("perfiles").update(datos_perfil).eq("id", user_id).execute()

        # 2. Si cambió correo o contraseña, actualizar en Auth también
        auth_update = {}
        if nuevo_correo:
            auth_update["email"] = nuevo_correo
        if nueva_password:
            auth_update["password"] = nueva_password
        if auth_update:
            sb_admin.auth.admin.update_user_by_id(user_id, auth_update)

        return True, "ok"
    except Exception as e:
        return False, str(e)


def get_slots_todos_docentes() -> list[dict]:
    """Para admin: todos los slots de todos los docentes con sus alumnos."""
    sb = get_supabase()
    try:
        res = (sb.table("disponibilidad_docentes")
                 .select("*, materias(nombre)")
                 .order("fecha", desc=True)
                 .order("hora_inicio", desc=True)
                 .execute())
        todos = res.data or []
        resultado = []
        cache_doc = {}
        for s in todos:
            m = s.get("materias", {})
            if isinstance(m, list): m = m[0] if m else {}
            s["materia_nombre"] = m.get("nombre", "—") if m else "—"
            s["hora_inicio"]    = str(s.get("hora_inicio",""))[:5]
            s["hora_fin"]       = str(s.get("hora_fin",""))[:5]
            # Nombre del docente
            did = s.get("docente_id","")
            if did not in cache_doc:
                cache_doc[did] = _get_nombre(did)
            info = cache_doc[did]
            s["docente_nombre"] = f"{info.get('nombre','')} {info.get('apellido','')}".strip() or "—"

            # Alumnos del slot
            ses_res = (sb.table("sesiones_tutoria")
                         .select("id, alumno_id, estado, asistencia, materia, descripcion")
                         .eq("disponibilidad_id", s["id"])
                         .neq("estado", "Cancelada")
                         .execute())
            alumnos = []
            for ses in (ses_res.data or []):
                info_a = _get_nombre(ses.get("alumno_id",""))
                ses["alumno_nombre"]  = f"{info_a.get('nombre','')} {info_a.get('apellido','')}".strip() or "—"
                ses["alumno_control"] = info_a.get("numero_control") or "—"
                alumnos.append(ses)

            # Contador real desde sesiones activas (no del campo cupos_usados)
            s["cupos_usados"] = len(alumnos)
            s["cupos"]        = CUPOS_MAX
            s["cupos_libres"] = CUPOS_MAX - len(alumnos)
            s["alumnos"]      = alumnos
            resultado.append(s)

        return resultado
    except Exception as e:
        st.error(f"Error al obtener slots globales: {e}")
        return []

def eliminar_usuario(user_id: str) -> bool:
    sb_admin = get_supabase_admin()
    try:
        sb_admin.auth.admin.delete_user(user_id)
        return True
    except Exception as e:
        st.error(f"Error al eliminar usuario: {e}")
        return False
