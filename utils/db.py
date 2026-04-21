"""
utils/db.py — Plataforma de Tutorías Académicas ITMH
"""
from __future__ import annotations
import streamlit as st
from utils.supabase_client import get_supabase
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
                 .eq("id", user_id)
                 .single()
                 .execute())
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
    """Materias asignadas a un docente."""
    sb = get_supabase()
    try:
        res = (sb.table("docente_materias")
                 .select("materia_id, materias(id, nombre)")
                 .eq("docente_id", docente_id)
                 .execute())
        materias = []
        for row in (res.data or []):
            m = row.get("materias", {})
            if isinstance(m, list):
                m = m[0] if m else {}
            if m:
                materias.append(m)
        return sorted(materias, key=lambda x: x.get("nombre", ""))
    except Exception as e:
        st.error(f"Error al obtener materias del docente: {e}")
        return []


def asignar_materia_docente(docente_id: str, materia_id: str) -> bool:
    sb = get_supabase()
    try:
        sb.table("docente_materias").insert(
            {"docente_id": docente_id, "materia_id": materia_id}
        ).execute()
        return True
    except Exception as e:
        st.error(f"Error al asignar materia: {e}")
        return False


def quitar_materia_docente(docente_id: str, materia_id: str) -> bool:
    sb = get_supabase()
    try:
        sb.table("docente_materias").delete()\
            .eq("docente_id", docente_id)\
            .eq("materia_id", materia_id).execute()
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
            "docente_id":  docente_id,
            "fecha":       fecha.isoformat(),
            "hora_inicio": hora_inicio.strftime("%H:%M"),
            "hora_fin":    hora_fin.strftime("%H:%M"),
            "materia_id":  materia_id,
            "cupos":       cupos,
            "cupos_usados": 0,
            "disponible":  True,
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
                 .order("fecha").order("hora_inicio")
                 .execute())
        slots = res.data or []
        for s in slots:
            m = s.get("materias", {})
            if isinstance(m, list):
                m = m[0] if m else {}
            s["materia_nombre"] = m.get("nombre", "—") if m else "—"
        return slots
    except Exception as e:
        st.error(f"Error al obtener disponibilidad: {e}")
        return []


def get_disponibilidad_por_materia(materia_id: str) -> list[dict]:
    """Slots libres con cupos disponibles para una materia."""
    sb = get_supabase()
    try:
        res = (sb.table("disponibilidad_docentes")
                 .select("*")
                 .eq("materia_id", materia_id)
                 .eq("disponible", True)
                 .gte("fecha", date.today().isoformat())
                 .order("fecha").order("hora_inicio")
                 .execute())
        slots = res.data or []
        # Filtrar slots con cupos reales disponibles
        slots = [s for s in slots if (s.get("cupos", 8) - s.get("cupos_usados", 0)) > 0]
        # Resolver nombre del docente
        cache = {}
        for s in slots:
            did = s.get("docente_id", "")
            if did not in cache:
                cache[did] = _get_nombre(did)
            info = cache[did]
            s["docente_nombre"] = f"{info.get('nombre','')} {info.get('apellido','')}".strip() or "Docente"
            s["cupos_libres"] = s.get("cupos", 8) - s.get("cupos_usados", 0)
        return slots
    except Exception as e:
        st.error(f"Error al obtener disponibilidad por materia: {e}")
        return []


def get_disponibilidad_libre() -> list[dict]:
    sb = get_supabase()
    try:
        res = (sb.table("disponibilidad_docentes")
                 .select("*, materias(nombre)")
                 .eq("disponible", True)
                 .gte("fecha", date.today().isoformat())
                 .order("fecha").order("hora_inicio")
                 .execute())
        slots = res.data or []
        slots = [s for s in slots if (s.get("cupos", 8) - s.get("cupos_usados", 0)) > 0]
        cache = {}
        for s in slots:
            did = s.get("docente_id", "")
            if did not in cache:
                cache[did] = _get_nombre(did)
            info = cache[did]
            s["docente_nombre"] = f"{info.get('nombre','')} {info.get('apellido','')}".strip() or "Docente"
            m = s.get("materias", {})
            if isinstance(m, list):
                m = m[0] if m else {}
            s["materia_nombre"] = m.get("nombre", "—") if m else "—"
            s["cupos_libres"] = s.get("cupos", 8) - s.get("cupos_usados", 0)
        return slots
    except Exception as e:
        st.error(f"Error al obtener disponibilidad libre: {e}")
        return []


# ─────────────────────────────────────────────────────────
# SESIONES
# ─────────────────────────────────────────────────────────

def agendar_sesion(alumno_id: str, docente_id: str,
                   disponibilidad_id: str, fecha_hora: str,
                   materia: str, descripcion: str) -> bool:
    sb = get_supabase()
    try:
        # Verificar cupos antes de insertar
        slot = sb.table("disponibilidad_docentes")\
                  .select("cupos, cupos_usados")\
                  .eq("id", disponibilidad_id).single().execute()
        if slot.data:
            cupos       = slot.data.get("cupos", 8)
            cupos_usados = slot.data.get("cupos_usados", 0)
            if cupos_usados >= cupos:
                st.error("Este horario ya no tiene cupos disponibles.")
                return False

        sb.table("sesiones_tutoria").insert({
            "alumno_id":        alumno_id,
            "docente_id":       docente_id,
            "disponibilidad_id": disponibilidad_id,
            "fecha_hora":       fecha_hora,
            "materia":          materia,
            "descripcion":      descripcion,
            "estado":           "Programada",
        }).execute()

        # Incrementar cupos_usados
        nuevo_usado = cupos_usados + 1
        nuevo_disp  = nuevo_usado < cupos
        sb.table("disponibilidad_docentes").update({
            "cupos_usados": nuevo_usado,
            "disponible":   nuevo_disp,
        }).eq("id", disponibilidad_id).execute()
        return True
    except Exception as e:
        st.error(f"Error al agendar sesión: {e}")
        return False


def cancelar_sesion(sesion_id: str, disponibilidad_id: str | None) -> bool:
    sb = get_supabase()
    try:
        sb.table("sesiones_tutoria").update({"estado": "Cancelada"}).eq("id", sesion_id).execute()
        if disponibilidad_id:
            slot = sb.table("disponibilidad_docentes")\
                      .select("cupos, cupos_usados")\
                      .eq("id", disponibilidad_id).single().execute()
            if slot.data:
                nuevo_usado = max(0, slot.data.get("cupos_usados", 1) - 1)
                sb.table("disponibilidad_docentes").update({
                    "cupos_usados": nuevo_usado,
                    "disponible":   True,
                }).eq("id", disponibilidad_id).execute()
        return True
    except Exception as e:
        st.error(f"Error al cancelar: {e}")
        return False


def get_sesiones_alumno(alumno_id: str) -> list[dict]:
    sb = get_supabase()
    try:
        res = (sb.table("sesiones_tutoria")
                 .select("*").eq("alumno_id", alumno_id)
                 .order("fecha_hora", desc=True).execute())
        return _enriquecer_sesiones_alumno(res.data or [])
    except Exception as e:
        st.error(f"Error al obtener sesiones: {e}")
        return []


def get_sesiones_docente(docente_id: str) -> list[dict]:
    sb = get_supabase()
    try:
        res = (sb.table("sesiones_tutoria")
                 .select("*").eq("docente_id", docente_id)
                 .order("fecha_hora", desc=True).execute())
        return _enriquecer_sesiones_docente(res.data or [])
    except Exception as e:
        st.error(f"Error al obtener sesiones: {e}")
        return []


def get_alumnos_por_slot(disponibilidad_id: str) -> list[dict]:
    """Todos los alumnos que reservaron un slot específico."""
    sb = get_supabase()
    try:
        res = (sb.table("sesiones_tutoria")
                 .select("id, alumno_id, estado, asistencia, notas_docente")
                 .eq("disponibilidad_id", disponibilidad_id)
                 .neq("estado", "Cancelada")
                 .execute())
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
    sb = get_supabase()
    try:
        estado = "Completada" if asistio else "No asistió"
        sb.table("sesiones_tutoria").update({
            "asistencia":    asistio,
            "estado":        estado,
            "notas_docente": notas,
        }).eq("id", sesion_id).execute()
        return True
    except Exception as e:
        st.error(f"Error al registrar asistencia: {e}")
        return False


def get_slots_pasados_docente(docente_id: str) -> list[dict]:
    """Slots cuya fecha y hora ya pasaron (para registrar asistencia)."""
    sb = get_supabase()
    try:
        ahora = datetime.now()
        res = (sb.table("disponibilidad_docentes")
                 .select("*, materias(nombre)")
                 .eq("docente_id", docente_id)
                 .execute())
        todos = res.data or []
        pasados = []
        for s in todos:
            try:
                fecha_hora_slot = datetime.strptime(
                    f"{s['fecha']} {s['hora_fin']}", "%Y-%m-%d %H:%M"
                )
                if fecha_hora_slot < ahora:
                    m = s.get("materias", {})
                    if isinstance(m, list):
                        m = m[0] if m else {}
                    s["materia_nombre"] = m.get("nombre", "—") if m else "—"
                    pasados.append(s)
            except Exception:
                pass
        return sorted(pasados, key=lambda x: x["fecha"] + x["hora_inicio"], reverse=True)
    except Exception as e:
        st.error(f"Error al obtener slots pasados: {e}")
        return []


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


def crear_usuario_completo(nombre: str, apellido: str, correo: str,
                           password: str, rol: str,
                           numero_control: str = None,
                           departamento: str = None) -> tuple[bool, str]:
    """Crea usuario en Supabase Auth + perfil en tabla perfiles."""
    sb = get_supabase()
    try:
        res = sb.auth.admin.create_user({
            "email":            correo,
            "password":         password,
            "email_confirm":    True,
            "user_metadata": {
                "nombre":   nombre,
                "apellido": apellido,
                "rol":      rol,
            }
        })
        if res.user:
            sb.table("perfiles").upsert({
                "id":             res.user.id,
                "nombre":         nombre,
                "apellido":       apellido,
                "correo":         correo,
                "rol":            rol,
                "numero_control": numero_control,
                "departamento":   departamento,
                "activo":         True,
            }).execute()
            return True, res.user.id
        return False, "No se pudo crear el usuario."
    except Exception as e:
        return False, str(e)


def eliminar_usuario(user_id: str) -> bool:
    sb = get_supabase()
    try:
        sb.auth.admin.delete_user(user_id)
        return True
    except Exception as e:
        st.error(f"Error al eliminar usuario: {e}")
        return False
