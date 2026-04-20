"""
utils/db.py
Funciones CRUD para todas las entidades de la plataforma.
"""
from __future__ import annotations
import streamlit as st
from utils.supabase_client import get_supabase
from datetime import date, time


# ─────────────────────────────────────────────────────────
# HELPERS INTERNOS
# ─────────────────────────────────────────────────────────

def _get_nombre(user_id: str) -> dict:
    """Retorna nombre, apellido y numero_control de un perfil."""
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
        # Mostrar el error real para diagnosticar problemas de RLS
        st.warning(f"⚠️ No se pudo leer perfil {user_id[:8]}…: {e}")
        return {}


def _enriquecer_sesiones_alumno(sesiones: list[dict]) -> list[dict]:
    """Agrega docente_nombre a cada sesion del alumno."""
    cache = {}
    for s in sesiones:
        did = s.get("docente_id", "")
        if did not in cache:
            cache[did] = _get_nombre(did)
        info = cache[did]
        s["docente_nombre"] = (
            f"{info.get('nombre','')} {info.get('apellido','')}".strip()
            or f"[id:{did[:8]}]"
        )
    return sesiones


def _enriquecer_sesiones_docente(sesiones: list[dict]) -> list[dict]:
    """Agrega alumno_nombre y alumno_control a cada sesion del docente."""
    cache = {}
    for s in sesiones:
        aid = s.get("alumno_id", "")
        if aid not in cache:
            cache[aid] = _get_nombre(aid)
        info = cache[aid]
        s["alumno_nombre"]  = (
            f"{info.get('nombre','')} {info.get('apellido','')}".strip()
            or f"[id:{aid[:8]}]"
        )
        s["alumno_control"] = info.get("numero_control") or "—"
    return sesiones


# ─────────────────────────────────────────────────────────
# DISPONIBILIDAD
# ─────────────────────────────────────────────────────────

def agregar_disponibilidad(docente_id: str, fecha: date,
                           hora_inicio: time, hora_fin: time) -> bool:
    sb = get_supabase()
    try:
        sb.table("disponibilidad_docentes").insert({
            "docente_id": docente_id,
            "fecha": fecha.isoformat(),
            "hora_inicio": hora_inicio.strftime("%H:%M"),
            "hora_fin": hora_fin.strftime("%H:%M"),
            "disponible": True,
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
                 .select("*")
                 .eq("docente_id", docente_id)
                 .order("fecha")
                 .order("hora_inicio")
                 .execute())
        return res.data or []
    except Exception as e:
        st.error(f"Error al obtener disponibilidad: {e}")
        return []


def get_disponibilidad_libre() -> list[dict]:
    """Slots disponibles con nombre del docente resuelto."""
    sb = get_supabase()
    try:
        res = (sb.table("disponibilidad_docentes")
                 .select("*")
                 .eq("disponible", True)
                 .gte("fecha", date.today().isoformat())
                 .order("fecha")
                 .order("hora_inicio")
                 .execute())
        slots = res.data or []
        cache = {}
        for s in slots:
            did = s.get("docente_id", "")
            if did not in cache:
                cache[did] = _get_nombre(did)
            info = cache[did]
            s["docente_nombre"] = (
                f"{info.get('nombre','')} {info.get('apellido','')}".strip()
                or f"[id:{did[:8]}]"
            )
        return slots
    except Exception as e:
        st.error(f"Error al obtener disponibilidad libre: {e}")
        return []


def get_docentes() -> list[dict]:
    sb = get_supabase()
    try:
        res = (sb.table("perfiles")
                 .select("id, nombre, apellido, departamento")
                 .eq("rol", "docente")
                 .eq("activo", True)
                 .execute())
        return res.data or []
    except Exception as e:
        st.error(f"Error al obtener docentes: {e}")
        return []


# ─────────────────────────────────────────────────────────
# SESIONES
# ─────────────────────────────────────────────────────────

def agendar_sesion(alumno_id: str, docente_id: str,
                   disponibilidad_id: str, fecha_hora: str,
                   materia: str, descripcion: str) -> bool:
    sb = get_supabase()
    try:
        sb.table("sesiones_tutoria").insert({
            "alumno_id": alumno_id,
            "docente_id": docente_id,
            "disponibilidad_id": disponibilidad_id,
            "fecha_hora": fecha_hora,
            "materia": materia,
            "descripcion": descripcion,
            "estado": "Programada",
        }).execute()
        sb.table("disponibilidad_docentes").update(
            {"disponible": False}
        ).eq("id", disponibilidad_id).execute()
        return True
    except Exception as e:
        st.error(f"Error al agendar sesión: {e}")
        return False


def cancelar_sesion(sesion_id: str, disponibilidad_id: str | None) -> bool:
    sb = get_supabase()
    try:
        sb.table("sesiones_tutoria").update(
            {"estado": "Cancelada"}
        ).eq("id", sesion_id).execute()
        if disponibilidad_id:
            sb.table("disponibilidad_docentes").update(
                {"disponible": True}
            ).eq("id", disponibilidad_id).execute()
        return True
    except Exception as e:
        st.error(f"Error al cancelar: {e}")
        return False


def get_sesiones_alumno(alumno_id: str) -> list[dict]:
    sb = get_supabase()
    try:
        res = (sb.table("sesiones_tutoria")
                 .select("*")
                 .eq("alumno_id", alumno_id)
                 .order("fecha_hora", desc=True)
                 .execute())
        return _enriquecer_sesiones_alumno(res.data or [])
    except Exception as e:
        st.error(f"Error al obtener sesiones: {e}")
        return []


def get_sesiones_docente(docente_id: str) -> list[dict]:
    sb = get_supabase()
    try:
        res = (sb.table("sesiones_tutoria")
                 .select("*")
                 .eq("docente_id", docente_id)
                 .order("fecha_hora", desc=True)
                 .execute())
        return _enriquecer_sesiones_docente(res.data or [])
    except Exception as e:
        st.error(f"Error al obtener sesiones: {e}")
        return []


def registrar_asistencia(sesion_id: str, asistio: bool, notas: str = "") -> bool:
    sb = get_supabase()
    try:
        estado = "Completada" if asistio else "No asistió"
        sb.table("sesiones_tutoria").update({
            "asistencia": asistio,
            "estado": estado,
            "notas_docente": notas,
        }).eq("id", sesion_id).execute()
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
