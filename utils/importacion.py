"""
utils/importacion.py
Importación masiva de usuarios desde Excel.
Flujo: invite_user_by_email con redirect_to /activar
El usuario recibe el link, va a /activar y crea su propia contraseña.
"""
from __future__ import annotations
import io
import pandas as pd
import streamlit as st
from utils.db import crear_usuario_completo

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


def _norm(texto: str) -> str:
    if not texto:
        return ""
    tabla = str.maketrans("áéíóúüñÁÉÍÓÚÜÑ", "aeiouunAEIOUUN")
    return texto.strip().translate(tabla).lower()


def generar_correo_alumno(numero_control: str) -> str:
    return f"L{numero_control.strip()}@{DOMINIO}"


def generar_correo_docente(nombre: str, apellidos: str) -> str:
    primer_nombre = _norm(nombre.strip().split()[0])
    partes        = apellidos.strip().split()
    inicial1      = _norm(partes[0])[0] if len(partes) >= 1 else ""
    inicial2      = _norm(partes[1])[0] if len(partes) >= 2 else ""
    return f"{primer_nombre}.{inicial1}{inicial2}@{DOMINIO}"


def _limpiar(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    return str(val).strip()


def _validar_alumno(fila: dict, num: int) -> list[str]:
    errs = []
    if not _limpiar(fila.get("nombre")):         errs.append(f"Fila {num}: Nombre vacío.")
    if not _limpiar(fila.get("apellidos")):      errs.append(f"Fila {num}: Apellidos vacíos.")
    if not _limpiar(fila.get("numero_control")): errs.append(f"Fila {num}: Número de control vacío.")
    return errs


def _validar_docente(fila: dict, num: int) -> list[str]:
    errs = []
    if not _limpiar(fila.get("nombre")):    errs.append(f"Fila {num}: Nombre vacío.")
    if not _limpiar(fila.get("apellidos")): errs.append(f"Fila {num}: Apellidos vacíos.")
    depto = _limpiar(fila.get("departamento"))
    if not depto:
        errs.append(f"Fila {num}: Departamento vacío.")
    elif depto not in DEPTOS_VALIDOS:
        errs.append(f"Fila {num}: Departamento '{depto}' no válido.")
    return errs


def leer_excel_alumnos(archivo_bytes: bytes) -> tuple[list[dict], list[str]]:
    errores, filas = [], []
    try:
        df = pd.read_excel(io.BytesIO(archivo_bytes), sheet_name="Alumnos",
                           header=2, dtype=str, usecols=[0, 1, 2])
        df.columns = ["nombre", "apellidos", "numero_control"]
        df = df.dropna(how="all")
        for i, row in df.iterrows():
            fila = {k: _limpiar(v) for k, v in row.items()}
            if not fila["nombre"] or fila["nombre"].lower().startswith("nombre"):
                continue
            errs = _validar_alumno(fila, i + 4)
            if errs:
                errores.extend(errs)
            else:
                fila["correo"] = generar_correo_alumno(fila["numero_control"])
                filas.append(fila)
    except Exception as e:
        errores.append(f"Error al leer hoja Alumnos: {e}")
    return filas, errores


def leer_excel_docentes(archivo_bytes: bytes) -> tuple[list[dict], list[str]]:
    errores, filas = [], []
    try:
        df = pd.read_excel(io.BytesIO(archivo_bytes), sheet_name="Docentes",
                           header=2, dtype=str, usecols=[0, 1, 2])
        df.columns = ["nombre", "apellidos", "departamento"]
        df = df.dropna(how="all")
        for i, row in df.iterrows():
            fila = {k: _limpiar(v) for k, v in row.items()}
            if not fila["nombre"] or fila["nombre"].lower().startswith("nombre"):
                continue
            errs = _validar_docente(fila, i + 4)
            if errs:
                errores.extend(errs)
            else:
                fila["correo"] = generar_correo_docente(fila["nombre"], fila["apellidos"])
                filas.append(fila)
    except Exception as e:
        errores.append(f"Error al leer hoja Docentes: {e}")
    return filas, errores


def importar_alumnos(filas: list[dict]) -> tuple[int, int, list[str], list[dict]]:
    exitosos, fallidos, errores, resumen = 0, 0, [], []
    barra = st.progress(0, text="Enviando invitaciones a alumnos…")
    for idx, fila in enumerate(filas):
        ok, resultado = crear_usuario_completo(
            nombre=fila["nombre"], apellido=fila["apellidos"],
            correo=fila["correo"], password="",
            rol="alumno", numero_control=fila["numero_control"],
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
            errores.append(f"{fila['nombre']} {fila['apellidos']} ({fila['correo']}): {resultado}")
            resumen.append({
                "Nombre":      f"{fila['nombre']} {fila['apellidos']}",
                "No. Control": fila["numero_control"],
                "Correo":      fila["correo"],
                "Estado":      f"❌ {resultado}",
            })
        barra.progress((idx + 1) / len(filas), text=f"Procesando {idx+1}/{len(filas)}…")
    barra.empty()
    return exitosos, fallidos, errores, resumen


def importar_docentes(filas: list[dict]) -> tuple[int, int, list[str], list[dict]]:
    exitosos, fallidos, errores, resumen = 0, 0, [], []
    barra = st.progress(0, text="Enviando invitaciones a docentes…")
    for idx, fila in enumerate(filas):
        ok, resultado = crear_usuario_completo(
            nombre=fila["nombre"], apellido=fila["apellidos"],
            correo=fila["correo"], password="",
            rol="docente", departamento=fila["departamento"],
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
            errores.append(f"{fila['nombre']} {fila['apellidos']} ({fila['correo']}): {resultado}")
            resumen.append({
                "Nombre":       f"{fila['nombre']} {fila['apellidos']}",
                "Departamento": fila["departamento"],
                "Correo":       fila["correo"],
                "Estado":       f"❌ {resultado}",
            })
        barra.progress((idx + 1) / len(filas), text=f"Procesando {idx+1}/{len(filas)}…")
    barra.empty()
    return exitosos, fallidos, errores, resumen
