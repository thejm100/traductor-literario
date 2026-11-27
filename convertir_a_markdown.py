"""
=============================================================================
CONVERSOR DE LIBROS A MARKDOWN (Basado en Microsoft MarkItDown)
=============================================================================
Herramienta para convertir libros en PDF, Word (.docx), etc., a Markdown (.md)
limpio y optimizado para el Agente de Traducción de IA.

Ventajas:
  - Extrae el texto una sola vez (evita re-procesar el PDF a cada rato).
  - Permite al traductor revisar o editar el texto original antes de traducir.
  - El agente de traducción arranca en milisegundos leyendo directamente el .md.
=============================================================================
"""

import os
import re
import sys
from markitdown import MarkItDown

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def limpiar_texto_literario(texto_md: str) -> str:
    """
    Aplica normalización literaria al Markdown generado:
    - Une palabras partidas por guiones de imprenta al final de línea.
    - Une saltos de línea artificiales dentro de un mismo párrafo.
    - Filtra números de página aislados y cornisas repetitivas.
    """
    lineas = texto_md.splitlines()
    lineas_limpias = []

    for linea in lineas:
        linea_strip = linea.strip()
        # Omitir números de página aislados
        if re.match(r"^\s*\d+\s*$", linea_strip):
            continue
        # Omitir encabezados de cornisa repetitivos comunes
        if re.match(r"^\s*(CONFESSION OF FAITH|PREFACE)\.?\s*$", linea_strip, re.IGNORECASE):
            continue
        lineas_limpias.append(linea)

    texto = "\n".join(lineas_limpias)

    # 1. Unir palabras divididas con guiones (ej. 'repro- bates' -> 'reprobates')
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

def convertir_archivo_a_markdown(ruta_entrada: str = None, ruta_salida: str = None):
    print("\n" + "="*70)
    print("      MICROSOFT MARKITDOWN - CONVERSOR DE LIBROS A MARKDOWN")
    print("="*70)

    # Detección por defecto del libro en PDF si no se pasa ruta
    if not ruta_entrada:
        pdf_defecto = os.path.join(BASE_DIR, "Confession of Faith for Cumberland Presbyterians 1883.pdf")
        if os.path.exists(pdf_defecto):
            print(f"[i] Archivo detectado: '{os.path.basename(pdf_defecto)}'")
            eleccion = input("Presiona Enter para convertir este archivo (o escribe otra ruta): ").strip()
            ruta_entrada = eleccion.strip('"\'') if eleccion else pdf_defecto
        else:
            ruta_entrada = input("Ingresa la ruta de tu PDF o DOCX a convertir: ").strip().strip('"\'')

    if not os.path.exists(ruta_entrada):
        print(f"[X] Error: No se encontró el archivo: '{ruta_entrada}'")
        return None

    if not ruta_salida:
        nombre_base = os.path.splitext(os.path.basename(ruta_entrada))[0]
        ruta_salida = os.path.join(BASE_DIR, f"{nombre_base}_fuente.md")

    print(f"\n⏳ Extrayendo contenido con Microsoft MarkItDown...")
    md = MarkItDown()
    resultado = md.convert(ruta_entrada)
    texto_crudo = resultado.text_content

    print(f"⏳ Aplicando normalización literaria y unión de párrafos...")
    texto_final = limpiar_texto_literario(texto_crudo)

    with open(ruta_salida, "w", encoding="utf-8") as f:
        f.write(texto_final)

    total_palabras = len(texto_final.split())
    total_parrafos = len(texto_final.split("\n\n"))

    print("\n" + "="*70)
    print(f" [✓] ¡CONVERSIÓN COMPLETADA CON ÉXITO!")
    print("="*70)
    print(f" 📄 Archivo Markdown generado: '{os.path.basename(ruta_salida)}'")
    print(f" 📊 Total de palabras: {total_palabras:,}")
    print(f" 📑 Total de párrafos limpios: {total_parrafos:,}")
    print(f" 💡 Ahora puedes abrir '{os.path.basename(ruta_salida)}' para revisarlo si lo deseas.")
    print("="*70)

    return ruta_salida

if __name__ == "__main__":
    convertir_archivo_a_markdown()
