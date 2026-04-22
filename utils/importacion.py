"""
utils/importacion.py
Importación masiva de usuarios desde Excel.
Flujo: invite_user_by_email — el usuario recibe el link y crea su propia contraseña.
"""
from __future__ import annotations
import io
import pandas as pd
import streamlit as st
from utils.supabase_client import get_supabase_admin

DOMINIO = "matehuala.tecnm.mx"

DEPTOS_VALIDOS = [
    "Ingeniería en Sistemas Computacionales",
    "Ciencias Básicas",
    "Ingeniería Industrial",
    "Ingeniería Eléctrica",
    "Ingeniería Mecánica",
    "Coordinación Académica",
    "Administración",
    "Otro",
]


# ─────────────────────────────────────────────────────────
# GENERACIÓN DE CORREOS
# ─────────────────────────────────────────────────────────

def _norm(texto: str) -> str:
    """Quita acentos y convierte a minúsculas."""
    if not texto:
        return ""
    tabla = str.maketrans("áéíóúüñÁÉÍÓÚÜÑ", "aeiouunAEIOUUN")
    return texto.strip().translate(tabla).lower()


def generar_correo_alumno(numero_control: str) -> str:
    """L{numero_control}@matehuala.tecnm.mx"""
    return f"L{numero_control.strip()}@{DOMINIO}"


def generar_correo_docente(nombre: str, apellidos: str) -> str:
    """primernombre.{inicialAp1}{inicialAp2}@matehuala.tecnm.mx"""
    primer_nombre = _norm(nombre.strip().split()[0])
    partes        = apellidos.strip().split()
    inicial1      = _norm(partes[0])[0] if len(partes) >= 1 else ""
    inicial2      = _norm(partes[1])[0] if len(partes) >= 2 else ""
    return f"{primer_nombre}.{inicial1}{inicial2}@{DOMINIO}"


def _limpiar(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    return str(val).strip()


# ─────────────────────────────────────────────────────────
# VALIDACIÓN
# ─────────────────────────────────────────────────────────

def _validar_alumno(fila: dict, num: int) -> list[str]:
    errs = []
    if not _limpiar(fila.get("nombre")):
        errs.append(f"Fila {num}: Nombre vacío.")
    if not _limpiar(fila.get("apellidos")):
        errs.append(f"Fila {num}: Apellidos vacíos.")
    if not _limpiar(fila.get("numero_control")):
        errs.append(f"Fila {num}: Número de control vacío.")
    return errs


def _validar_docente(fila: dict, num: int) -> list[str]:
    errs = []
    if not _limpiar(fila.get("nombre")):
        errs.append(f"Fila {num}: Nombre vacío.")
    if not _limpiar(fila.get("apellidos")):
        errs.append(f"Fila {num}: Apellidos vacíos.")
    depto = _limpiar(fila.get("departamento"))
    if not depto:
        errs.append(f"Fila {num}: Departamento vacío.")
    elif depto not in DEPTOS_VALIDOS:
        errs.append(
            f"Fila {num}: Departamento '{depto}' no válido. "
            f"Revisa la hoja 'Referencia'."
        )
    return errs


# ─────────────────────────────────────────────────────────
# LEER EXCEL
# ─────────────────────────────────────────────────────────

def leer_excel_alumnos(archivo_bytes: bytes) -> tuple[list[dict], list[str]]:
    """
    Lee hoja 'Alumnos'. Columnas (fila 3):
    Nombre(s) | Apellidos | Número de Control
    """
    errores = []
    filas   = []
    try:
        df = pd.read_excel(
            io.BytesIO(archivo_bytes),
            sheet_name="Alumnos",
            header=2,
            dtype=str,
            usecols=[0, 1, 2],
        )
        df.columns = ["nombre", "apellidos", "numero_control"]
        df = df.dropna(how="all")

        for i, row in df.iterrows():
            fila = {k: _limpiar(v) for k, v in row.items()}
            if not fila["nombre"] or fila["nombre"].lower().startswith("nombre"):
                continue
            num_fila = i + 4
            errs = _validar_alumno(fila, num_fila)
            if errs:
                errores.extend(errs)
            else:
                fila["correo"] = generar_correo_alumno(fila["numero_control"])
                filas.append(fila)
    except Exception as e:
        errores.append(f"Error al leer hoja Alumnos: {e}")
    return filas, errores


def leer_excel_docentes(archivo_bytes: bytes) -> tuple[list[dict], list[str]]:
    """
    Lee hoja 'Docentes'. Columnas (fila 3):
    Nombre(s) | Apellidos | Departamento
    """
    errores = []
    filas   = []
    try:
        df = pd.read_excel(
            io.BytesIO(archivo_bytes),
            sheet_name="Docentes",
            header=2,
            dtype=str,
            usecols=[0, 1, 2],
        )
        df.columns = ["nombre", "apellidos", "departamento"]
        df = df.dropna(how="all")

        for i, row in df.iterrows():
            fila = {k: _limpiar(v) for k, v in row.items()}
            if not fila["nombre"] or fila["nombre"].lower().startswith("nombre"):
                continue
            num_fila = i + 4
            errs = _validar_docente(fila, num_fila)
            if errs:
                errores.extend(errs)
            else:
                fila["correo"] = generar_correo_docente(fila["nombre"], fila["apellidos"])
                filas.append(fila)
    except Exception as e:
        errores.append(f"Error al leer hoja Docentes: {e}")
    return filas, errores


# ─────────────────────────────────────────────────────────
# INVITAR USUARIOS A SUPABASE
# ─────────────────────────────────────────────────────────

def _invitar_usuario(nombre: str, apellidos: str, correo: str,
                     rol: str, numero_control: str = None,
                     departamento: str = None) -> tuple[bool, str]:
    """
    Usa invite_user_by_email: Supabase envía el link de activación
    al correo del usuario. El usuario define su propia contraseña.
    """
    sb_admin = get_supabase_admin()
    try:
        res = sb_admin.auth.admin.invite_user_by_email(
            correo,
            options={
                "data": {
                    "nombre":   nombre,
                    "apellido": apellidos,
                    "rol":      rol,
                }
            }
        )
        if res.user:
            # Crear/actualizar perfil
            sb_admin.table("perfiles").upsert({
                "id":             res.user.id,
                "nombre":         nombre,
                "apellido":       apellidos,
                "correo":         correo,
                "rol":            rol,
                "numero_control": numero_control or None,
                "departamento":   departamento or None,
                "activo":         True,
            }).execute()
            return True, res.user.id
        return False, "No se recibió respuesta del servidor."
    except Exception as e:
        return False, str(e)


def importar_alumnos(filas: list[dict]) -> tuple[int, int, list[str], list[dict]]:
    """Invita alumnos masivamente. Retorna (exitosos, fallidos, errores, resumen)."""
    exitosos = 0
    fallidos = 0
    errores  = []
    resumen  = []
    total    = len(filas)
    barra    = st.progress(0, text="Enviando invitaciones a alumnos…")

    for idx, fila in enumerate(filas):
        ok, resultado = _invitar_usuario(
            nombre         = fila["nombre"],
            apellidos      = fila["apellidos"],
            correo         = fila["correo"],
            rol            = "alumno",
            numero_control = fila["numero_control"],
        )
        if ok:
            exitosos += 1
            resumen.append({
                "Nombre":      f"{fila['nombre']} {fila['apellidos']}",
                "No. Control": fila["numero_control"],
                "Correo":      fila["correo"],
                "Estado":      "✅ Invitación enviada",
            })
        else:
            fallidos += 1
            errores.append(
                f"{fila['nombre']} {fila['apellidos']} ({fila['correo']}): {resultado}"
            )
            resumen.append({
                "Nombre":      f"{fila['nombre']} {fila['apellidos']}",
                "No. Control": fila["numero_control"],
                "Correo":      fila["correo"],
                "Estado":      f"❌ {resultado}",
            })
        barra.progress((idx + 1) / total, text=f"Procesando {idx+1}/{total}…")

    barra.empty()
    return exitosos, fallidos, errores, resumen


def importar_docentes(filas: list[dict]) -> tuple[int, int, list[str], list[dict]]:
    """Invita docentes masivamente. Retorna (exitosos, fallidos, errores, resumen)."""
    exitosos = 0
    fallidos = 0
    errores  = []
    resumen  = []
    total    = len(filas)
    barra    = st.progress(0, text="Enviando invitaciones a docentes…")

    for idx, fila in enumerate(filas):
        ok, resultado = _invitar_usuario(
            nombre        = fila["nombre"],
            apellidos     = fila["apellidos"],
            correo        = fila["correo"],
            rol           = "docente",
            departamento  = fila["departamento"],
        )
        if ok:
            exitosos += 1
            resumen.append({
                "Nombre":       f"{fila['nombre']} {fila['apellidos']}",
                "Departamento": fila["departamento"],
                "Correo":       fila["correo"],
                "Estado":       "✅ Invitación enviada",
            })
        else:
            fallidos += 1
            errores.append(
                f"{fila['nombre']} {fila['apellidos']} ({fila['correo']}): {resultado}"
            )
            resumen.append({
                "Nombre":       f"{fila['nombre']} {fila['apellidos']}",
                "Departamento": fila["departamento"],
                "Correo":       fila["correo"],
                "Estado":       f"❌ {resultado}",
            })
        barra.progress((idx + 1) / total, text=f"Procesando {idx+1}/{total}…")

    barra.empty()
    return exitosos, fallidos, errores, resumen
