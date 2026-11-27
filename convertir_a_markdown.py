"""
=============================================================================
CONVERSOR DE LIBROS A MARKDOWN (Basado en Microsoft MarkItDown)
=============================================================================
Herramienta universal para convertir libros en PDF, Word (.docx), etc.,
a texto Markdown limpio y optimizado para el Agente de Traducción.

Ventajas:
  - Soporta subida dinámica de PDFs y documentos de cualquier usuario.
  - Normaliza errores de OCR, unión de palabras cortadas y saltos de imprenta.
  - El agente arranca en milisegundos trabajando sobre bloques lógicos limpios.
=============================================================================
"""

import os
import re
import sys
import tempfile
from markitdown import MarkItDown

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def limpiar_texto_literario(texto_md: str) -> str:
    """
    Aplica normalización literaria al Markdown generado:
    - Une palabras partidas por guiones de imprenta al final de línea (ej. Westmin- ster -> Westminster).
    - Une saltos de línea artificiales dentro de un mismo párrafo.
    - Filtra números de página aislados y cornisas repetitivas de escaneo.
    """
    if not texto_md:
        return ""

    lineas = texto_md.splitlines()
    lineas_limpias = []

    for linea in lineas:
        linea_strip = linea.strip()
        # Omitir números de página aislados
        if re.match(r"^\s*\d+\s*$", linea_strip):
            continue
        lineas_limpias.append(linea)

    texto = "\n".join(lineas_limpias)

    # 1. Unir palabras divididas con guiones de imprenta (ej. 'repro- bates' -> 'reprobates')
    texto = re.sub(r"(\b\w+)-\s*\n\s*(\w+\b)", r"\1\2", texto)
    texto = re.sub(r"(\b\w+)-\s+(\w+\b)", r"\1\2", texto)

    # 2. Unir saltos de línea simples dentro de párrafos preservando párrafos dobles
    parrafos = texto.split("\n\n")
    parrafos_unidos = []
    for p in parrafos:
        p_limpio = re.sub(r"(?<!\n)\n(?!\n)", " ", p.strip())
        p_limpio = re.sub(r"[ \t]+", " ", p_limpio)
        if p_limpio:
            parrafos_unidos.append(p_limpio)

    return "\n\n".join(parrafos_unidos)


def extraer_texto_de_archivo_o_buffer(archivo_o_ruta, nombre_archivo: str = "") -> str:
    """
    Extrae y normaliza el texto de cualquier archivo (ruta local o buffer en memoria de Streamlit).
    Soporta PDF, DOCX, MD, TXT, etc.
    """
    # Caso 1: Es una ruta en disco existente
    if isinstance(archivo_o_ruta, str) and os.path.exists(archivo_o_ruta):
        nombre = os.path.basename(archivo_o_ruta).lower()
        if nombre.endswith((".md", ".txt")):
            with open(archivo_o_ruta, "r", encoding="utf-8", errors="replace") as f:
                return limpiar_texto_literario(f.read())
        else:
            md = MarkItDown()
            res = md.convert(archivo_o_ruta)
            return limpiar_texto_literario(res.text_content)

    # Caso 2: Es un objeto en memoria (Streamlit UploadedFile o BytesIO)
    nombre = (nombre_archivo or getattr(archivo_o_ruta, "name", "documento")).lower()

    if nombre.endswith((".md", ".txt")):
        if hasattr(archivo_o_ruta, "getvalue"):
            raw_bytes = archivo_o_ruta.getvalue()
        elif hasattr(archivo_o_ruta, "read"):
            raw_bytes = archivo_o_ruta.read()
        else:
            raw_bytes = bytes(archivo_o_ruta)
        try:
            texto = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            texto = raw_bytes.decode("latin-1", errors="replace")
        return limpiar_texto_literario(texto)

    # Para binarios (PDF, DOCX) usamos un archivo temporal para MarkItDown
    ext = os.path.splitext(nombre)[1] or ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_f:
        temp_path = temp_f.name
        if hasattr(archivo_o_ruta, "getbuffer"):
            temp_f.write(archivo_o_ruta.getbuffer())
        elif hasattr(archivo_o_ruta, "getvalue"):
            temp_f.write(archivo_o_ruta.getvalue())
        elif hasattr(archivo_o_ruta, "read"):
            temp_f.write(archivo_o_ruta.read())
        else:
            temp_f.write(bytes(archivo_o_ruta))

    try:
        md = MarkItDown()
        resultado = md.convert(temp_path)
        texto = resultado.text_content
        return limpiar_texto_literario(texto)
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass


def convertir_archivo_a_markdown(ruta_entrada: str = None, ruta_salida: str = None):
    """Función de utilidad para CLI o scripts de lote."""
    if not ruta_entrada or not os.path.exists(ruta_entrada):
        print("[X] Archivo no especificado o inexistente.")
        return None

    if not ruta_salida:
        nombre_base = os.path.splitext(os.path.basename(ruta_entrada))[0]
        ruta_salida = os.path.join(BASE_DIR, f"{nombre_base}_fuente.md")

    texto = extraer_texto_de_archivo_o_buffer(ruta_entrada)
    with open(ruta_salida, "w", encoding="utf-8") as f:
        f.write(texto)

    return ruta_salida


if __name__ == "__main__":
    if len(sys.argv) > 1:
        convertir_archivo_a_markdown(sys.argv[1])
    else:
        print("Uso: python convertir_a_markdown.py <ruta_archivo>")
