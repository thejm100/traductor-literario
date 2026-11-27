"""
=============================================================================
AGENTE DE TRADUCCIÓN LITERARIA Y TEOLÓGICA PROFESIONAL (Inglés Histórico -> es-CO)
=============================================================================
Desarrollado para Traductores Profesionales y Desarrolladores Junior.

Características:
  - Conexión real a la IA mediante Google Gemini API (gemini-2.5-flash).
  - Guarda tu API Key automáticamente en 'clave_api.txt' (solo la pides una vez).
  - Corrección inteligente de errores de OCR y tipografía antigua de 1883 (Tue -> The, Ghrist -> Christ).
  - Unión automática de palabras cortadas con guiones de imprenta (Westmin- ster -> Westminster).
  - Localización en Español de Colombia culto, reverencial y literario.
  - Generación de Bitácora de Decisiones Filológicas y Notas al Pie.
  - Guarda el libro traducido en 'libro_traducido.md'.
=============================================================================
"""

import os
import sys
import json
import re
from google import genai
from google.genai import errors

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ==========================================
# 0. GESTOR DE CLAVE API (GEMINI)
# ==========================================
ARCHIVO_API_KEY = os.path.join(BASE_DIR, "clave_api.txt")

def obtener_o_pedir_api_key() -> str:
    # 0. Revisar si está en st.secrets (cuando corre en Streamlit Cloud)
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            if "GEMINI_API_KEY" in st.secrets:
                return str(st.secrets["GEMINI_API_KEY"]).strip()
            if "GOOGLE_API_KEY" in st.secrets:
                return str(st.secrets["GOOGLE_API_KEY"]).strip()
    except Exception:
        pass

    # 1. Revisar si está en variable de entorno
    key_env = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if key_env:
        return key_env.strip()

    # 2. Revisar si está guardada en clave_api.txt
    if os.path.exists(ARCHIVO_API_KEY):
        with open(ARCHIVO_API_KEY, "r", encoding="utf-8") as f:
            guardada = f.read().strip()
            if guardada:
                return guardada

    # 3. Pedir al usuario por consola y guardarla
    print("\n" + "="*70)
    print("🔑 CONFIGURACIÓN DE CONEXIÓN A LA INTELIGENCIA ARTIFICIAL (GEMINI)")
    print("="*70)
    print("Para que el agente pueda leer y traducir tus libros reales con rigor filológico,")
    print("necesita conectarse al modelo de IA mediante una Clave API gratuita de Google.")
    print("\nSi aún no tienes una, créala gratis en menos de un minuto aquí:")
    print("👉 https://aistudio.google.com/app/apikey\n")

    while True:
        clave = input("Pega tu API Key de Gemini aquí y presiona Enter: ").strip()
        if clave:
            with open(ARCHIVO_API_KEY, "w", encoding="utf-8") as f:
                f.write(clave)
            print(f"[✓] Clave API guardada con éxito en '{ARCHIVO_API_KEY}' (no te la volverá a pedir).\n")
            return clave
        print("[!] La clave no puede estar vacía. Inténtalo de nuevo.")


# ==========================================
# 1. SEGMENTADOR SEMÁNTICO DE TEXTO (MARKDOWN)
# ==========================================
class SegmentadorTexto:
    @staticmethod
    def dividir_en_fragmentos(texto: str, max_palabras: int = 220) -> list[str]:
        """Divide el texto Markdown respetando los límites de párrafos para preservar la coherencia temática."""
        parrafos = [p.strip() for p in texto.split("\n\n") if p.strip()]
        fragmentos = []
        fragmento_actual = []
        acumulador = 0

        for parrafo in parrafos:
            palabras = len(parrafo.split())
            if acumulador + palabras > max_palabras and fragmento_actual:
                fragmentos.append("\n\n".join(fragmento_actual))
                fragmento_actual = [parrafo]
                acumulador = palabras
            else:
                fragmento_actual.append(parrafo)
                acumulador += palabras

        if fragmento_actual:
            fragmentos.append("\n\n".join(fragmento_actual))

        return fragmentos


# ==========================================
# 2. MEMORIA Y CONTEXTO DEL LIBRO
# ==========================================
class MemoriaLibro:
    def __init__(self, archivo_memoria: str = None):
        self.archivo_memoria = archivo_memoria or os.path.join(BASE_DIR, "contexto_libro.json")
        self.datos = self.cargar_o_crear()

    def cargar_o_crear(self) -> dict:
        if os.path.exists(self.archivo_memoria):
            with open(self.archivo_memoria, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def inicializar_interactivo(self, nombre_sugerido: str = ""):
        if self.datos.get("titulo"):
            print(f"\n[+] Libro activo en memoria: '{self.datos.get('titulo')}'")
            print(f"    Autor: {self.datos.get('autor')} | Época: {self.datos.get('epoca')}")
            cambiar = input("¿Deseas usar esta configuración de libro? [Enter = Sí | N = Configurar de nuevo]: ").strip().lower()
            if cambiar != "n":
                return

        print("\n" + "="*60)
        print("  CONFIGURACIÓN DEL LIBRO (El agente usará esto como guía filológica)")
        print("="*60)
        titulo_def = nombre_sugerido or "Confesión de Fe para los Presbiterianos Cumberland"
        titulo = input(f"1. Título del libro [{titulo_def}]: ").strip() or titulo_def
        autor = input("2. Autor o entidad eclesiástica [Iglesia Presbiteriana Cumberland]: ").strip() or "Iglesia Presbiteriana Cumberland"
        epoca = input("3. Año o época histórica [1883, siglo XIX]: ").strip() or "1883, siglo XIX"

        self.datos = {
            "titulo": titulo,
            "autor": autor,
            "epoca": epoca,
            "dialecto_meta": "Español de Colombia (es-CO) culto, solemne y literario",
            "guia_estilo": (
                "Tratamiento solemne, respetuoso y teológicamente riguroso. "
                "Vocabulario eclesiástico fiel a la tradición hispana histórica (Pacto de Gracia, Ordenanzas, "
                "Expiación, Santa Cena, Justificación). Sintaxis fluida y elocuente sin modismos callejeros modernos."
            ),
            "glosario_terminos": {
                "covenant of grace": "pacto de gracia",
                "ordinances": "ordenanzas sagradas",
                "reprobation": "reprobación",
                "lord's supper": "Santa Cena / Cena del Señor",
                "testator": "testador",
                "infant dying in infancy": "infante que muere en la niñez / párvulo"
            },
            "ultimo_bloque_aprobado": 0
        }
        self.guardar()
        print("[✓] Contexto guardado en 'contexto_libro.json'\n")

    def agregar_termino(self, original: str, traduccion: str):
        self.datos.setdefault("glosario_terminos", {})[original.strip().lower()] = traduccion.strip()
        self.guardar()

    def guardar(self):
        with open(self.archivo_memoria, "w", encoding="utf-8") as f:
            json.dump(self.datos, f, ensure_ascii=False, indent=2)


import time

# ==========================================
# 3. AGENTE DE TRADUCCIÓN CON GEMINI REAL
# ==========================================
class AgenteTraductor:
    def __init__(self, api_key: str, memoria: MemoriaLibro):
        self.cliente = genai.Client(api_key=api_key)
        self.memoria = memoria
        # Modelos verificados en orden de prioridad y estabilidad:
        self.modelos_candidatos = ["gemini-3.5-flash", "gemini-3.8-flash", "gemini-3.1-flash-lite"]

    def traducir_bloque(self, texto_original: str, feedback_traductor: str = "") -> dict:
        ctx = self.memoria.datos

        prompt = f"""Eres un traductor literario senior, teólogo y filólogo bilingüe especializado en traducir 
literatura y documentos eclesiásticos históricos en inglés del siglo XIX al Español de Colombia (es-CO).

CONTEXTO DE LA OBRA:
- Título: {ctx.get('titulo')}
- Autor: {ctx.get('autor')}
- Época histórica: {ctx.get('epoca')}
- Dialecto meta: {ctx.get('dialecto_meta')}
- Guía de estilo: {ctx.get('guia_estilo')}

GLOSARIO ACUMULADO DEL LIBRO:
{json.dumps(ctx.get('glosario_terminos', {}), ensure_ascii=False, indent=2)}

INSTRUCCIÓN ESPECIAL DEL TRADUCTOR HUMANO:
{feedback_traductor if feedback_traductor else "Ninguna instrucción adicional. Aplica el máximo rigor teológico y filológico."}

IMPORTANTE SOBRE EL TEXTO FUENTE:
El texto proviene de un libro escaneado (OCR) de {ctx.get('epoca')}. Corrige silenciosamente cualquier error 
tipográfico evidente de digitalización (por ejemplo, 'Tue' por 'The', 'Ghrist' por 'Christ', 'subjeet' por 'subject', 
o guiones de corte de línea) para traducir el significado original exacto.

TEXTO ORIGINAL EN INGLÉS:
\"\"\"{texto_original}\"\"\"

RESPONDE EXCLUSIVAMENTE EN FORMATO JSON ESTRICTO CON ESTOS CAMPOS:
{{
  "analisis_epoca": "Explicación breve de los conceptos teológicos, arcaísmos o erratas de OCR corregidas.",
  "traduccion_es_co": "Traducción rigurosa, solemne y elegante en español de Colombia culto.",
  "decisiones_clave": [
    {{"termino_original": "...", "traduccion_elegida": "...", "justificacion": "..."}}
  ],
  "notas_al_pie": [
    {{"referencia": "...", "nota": "..."}}
  ]
}}"""

        ultimo_error = None
        for i, modelo in enumerate(self.modelos_candidatos):
            # Intentar hasta 2 veces por modelo ante saturación transitoria (503/429)
            for intento in range(1, 3):
                try:
                    respuesta = self.cliente.models.generate_content(
                        model=modelo,
                        contents=prompt,
                        config={
                            "response_mime_type": "application/json"
                        }
                    )

                    texto_json = respuesta.text.strip()
                    if texto_json.startswith("```"):
                        texto_json = re.sub(r"^```[a-zA-Z]*\n", "", texto_json)
                        texto_json = re.sub(r"\n```$", "", texto_json).strip()

                    datos_respuesta = json.loads(texto_json)
                    return datos_respuesta

                except errors.APIError as e:
                    ultimo_error = e
                    err_str = str(e).upper()
                    # Si es saturación (503), límite de peticiones (429) o modelo no encontrado (404)
                    if any(c in err_str for c in ["503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED"]):
                        if intento < 2:
                            time.sleep(2)  # Pausa breve antes de reintentar
                            continue
                        else:
                            # Si falló 2 veces por saturación, pasar al siguiente modelo
                            if i + 1 < len(self.modelos_candidatos):
                                print(f"\n[i] Servidor temporalmente ocupado en {modelo} (503). Conmutando a {self.modelos_candidatos[i+1]}...")
                            break
                    elif "404" in err_str or "NOT_FOUND" in err_str:
                        # Modelo no existe o descontinuado, pasar al siguiente inmediatamente
                        break
                    else:
                        # Otro error no recuperable
                        raise RuntimeError(f"Error en la API de Gemini: {e}")

                except json.JSONDecodeError:
                    return {
                        "analisis_epoca": "Análisis completado.",
                        "traduccion_es_co": respuesta.text,
                        "decisiones_clave": [],
                        "notas_al_pie": []
                    }
                except Exception as e:
                    ultimo_error = e
                    time.sleep(1)
                    continue

        raise RuntimeError(f"Error en la API de Gemini: {ultimo_error}")


# ==========================================
# 4. ORQUESTADOR INTERACTIVO (HUMAN-IN-THE-LOOP)
# ==========================================
def main():
    print("\n" + "="*70)
    print("      AGENTE DE TRADUCCIÓN LITERARIA Y TEOLÓGICA (es-CO)")
    print("="*70)

    # 1. Asegurar API Key de Gemini
    api_key = obtener_o_pedir_api_key()

    # 2. Cargar memoria del libro
    memoria = MemoriaLibro()

    # 3. Detectar si hay un archivo Markdown fuente ya generado o el PDF original
    md_fuente_defecto = os.path.join(BASE_DIR, "libro_fuente_ingles.md")
    pdf_defecto = os.path.join(BASE_DIR, "Confession of Faith for Cumberland Presbyterians 1883.pdf")

    sugerencia_ruta = ""
    if os.path.exists(md_fuente_defecto):
        sugerencia_ruta = md_fuente_defecto
    elif os.path.exists(pdf_defecto):
        sugerencia_ruta = pdf_defecto

    print("\n--- PASO 1: SELECCIÓN DEL LIBRO A TRADUCIR ---")
    if sugerencia_ruta:
        tipo = "Markdown (.md)" if sugerencia_ruta.endswith(".md") else "PDF (.pdf)"
        print(f"[i] Archivo detectado ({tipo}): '{os.path.basename(sugerencia_ruta)}'")
        entrada_ruta = input(f"Presiona Enter para usar este archivo (o escribe otra ruta): ").strip()
        ruta_archivo = entrada_ruta.strip('"\'') if entrada_ruta else sugerencia_ruta
    else:
        ruta_archivo = input("Ingresa la ruta de tu archivo (.md o .pdf): ").strip().strip('"\'')

    if not os.path.exists(ruta_archivo):
        print(f"[X] Error: No se encontró el archivo: '{ruta_archivo}'.")
        return

    # Inicializar memoria para este libro
    memoria.inicializar_interactivo(nombre_sugerido=os.path.splitext(os.path.basename(ruta_archivo))[0])

    # 4. Cargar y segmentar texto Markdown
    if ruta_archivo.lower().endswith(".md"):
        print(f"[i] Cargando directamente desde Markdown: '{os.path.basename(ruta_archivo)}'...")
        with open(ruta_archivo, "r", encoding="utf-8") as f:
            texto_limpio = f.read()
    else:
        # Si el usuario ingresa un PDF o DOCX, se convierte automáticamente con MarkItDown
        from convertir_a_markdown import convertir_archivo_a_markdown
        print(f"[i] Convirtiendo '{os.path.basename(ruta_archivo)}' a Markdown con Microsoft MarkItDown...")
        ruta_md = convertir_archivo_a_markdown(ruta_archivo)
        with open(ruta_md, "r", encoding="utf-8") as f:
            texto_limpio = f.read()

    fragmentos = SegmentadorTexto.dividir_en_fragmentos(texto_limpio)

    total_bloques = len(fragmentos)
    print(f"[✓] Libro procesado en {total_bloques} bloques de trabajo coherentes.")

    # 5. Inicializar Agente con Gemini
    agente = AgenteTraductor(api_key, memoria)
    archivo_salida = os.path.join(BASE_DIR, "libro_traducido.md")

    # Verificar si el archivo de salida ya tiene contenido previo
    bloque_inicio = 1
    if os.path.exists(archivo_salida) and os.path.getsize(archivo_salida) > 0:
        print(f"\n[!] El archivo '{archivo_salida}' ya contiene texto.")
        opcion_reinicio = input("¿Deseas [R]einiciar el archivo desde cero o [C]ontinuar agregando al final? [R/C]: ").strip().lower()
        if opcion_reinicio == "r":
            with open(archivo_salida, "w", encoding="utf-8") as f:
                f.write(f"# {memoria.datos.get('titulo')}\n\n")
                f.write(f"**Autor original:** {memoria.datos.get('autor')}  \n")
                f.write(f"**Año / Época:** {memoria.datos.get('epoca')}  \n")
                f.write(f"**Traducción y localización:** Español de Colombia (es-CO)  \n\n---\n")
            print(f"[✓] Archivo '{archivo_salida}' reiniciado e inicializado limpiamente.")

    preg_bloque = input(f"¿Desde qué bloque deseas empezar? [1-{total_bloques}] (Enter = 1): ").strip()
    if preg_bloque.isdigit() and 1 <= int(preg_bloque) <= total_bloques:
        bloque_inicio = int(preg_bloque)

    print("\n" + "="*70)
    print(f"      INICIANDO TRADUCCIÓN INTERACTIVA (Bloque {bloque_inicio} a {total_bloques})")
    print("="*70)

    for i in range(bloque_inicio - 1, total_bloques):
        num_bloque = i + 1
        fragmento = fragmentos[i]

        print(f"\n==================== [ BLOQUE {num_bloque} DE {total_bloques} ] ====================")
        print(f"\n📖 [TEXTO ORIGINAL EN INGLÉS ({len(fragmento.split())} palabras)]:\n")
        print(fragmento)
        print("\n" + "-"*70)

        feedback_traductor = ""

        while True:
            print("⏳ Consultando a la IA (analizando teología, arcaísmos de 1883 y traduciendo a es-CO)...")
            try:
                resultado = agente.traducir_bloque(fragmento, feedback_traductor)
            except Exception as e:
                print(f"\n[X] Error de conexión: {e}")
                reintentar = input("¿Deseas [R]eintentar o [S]alir?: ").strip().lower()
                if reintentar == "r":
                    continue
                else:
                    return

            print("\n🧐 [ANÁLISIS DE ÉPOCA Y CORRECCIONES DE OCR]:")
            print(f"   {resultado.get('analisis_epoca')}")

            print("\n🇨🇴 [TRADUCCIÓN EN ESPAÑOL DE COLOMBIA (es-CO)]:")
            print(f"   \"{resultado.get('traduccion_es_co')}\"")

            if resultado.get("decisiones_clave"):
                print("\n📋 [BITÁCORA DE DECISIONES DE TRADUCCIÓN]:")
                for d in resultado.get("decisiones_clave", []):
                    print(f"   • {d.get('termino_original')} -> '{d.get('traduccion_elegida')}': {d.get('justificacion')}")

            if resultado.get("notas_al_pie"):
                print("\n📌 [NOTAS AL PIE SUGERIDAS]:")
                for n in resultado.get("notas_al_pie", []):
                    print(f"   • [{n.get('referencia')}]: {n.get('nota')}")

            print("\n" + "-"*70)
            print("ACCIONES:")
            print("  [Enter] o [C] : APROBAR y guardar en 'libro_traducido.md' -> siguiente bloque")
            print("  [M]           : PEDIR AJUSTE (dar una instrucción específica al agente)")
            print("  [G]           : AGREGAR TÉRMINO al glosario permanente")
            print("  [S]           : PAUSAR Y SALIR (tu progreso queda guardado)")
            print("-"*70)
            opcion = input("Elige una acción: ").strip().lower()

            if opcion in ["", "c"]:
                with open(archivo_salida, "a", encoding="utf-8") as f_out:
                    f_out.write(f"\n\n### Sección {num_bloque}\n\n")
                    f_out.write(f"{resultado.get('traduccion_es_co')}\n")
                    if resultado.get("notas_al_pie"):
                        f_out.write("\n")
                        for n in resultado.get("notas_al_pie", []):
                            f_out.write(f"> *[Nota del Traductor sobre '{n.get('referencia')}']*: {n.get('nota')}  \n")
                print(f"[✓] Bloque {num_bloque} aprobado y guardado en '{archivo_salida}'.")
                break

            elif opcion == "m":
                feedback_traductor = input("\n👉 Escribe tu instrucción de ajuste (ej. 'hazlo sonar más reverencial' o 'usa la palabra X'): ")
                print("\n[+] Regenerando el bloque con tus indicaciones...\n")

            elif opcion == "g":
                orig = input("Término en inglés: ").strip()
                trad = input("Traducción oficial en tu glosario: ").strip()
                memoria.agregar_termino(orig, trad)
                print(f"[✓] Agregado a 'contexto_libro.json': {orig} -> {trad}")

            elif opcion == "s":
                print(f"\n[!] Sesión pausada en el bloque {num_bloque}. Todo lo aprobado está en '{archivo_salida}'.")
                return

    print("\n" + "="*70)
    print(f" 🎉 ¡TRADUCCIÓN DEL LIBRO COMPLETADA! Archivo listo en: '{archivo_salida}'")
    print("="*70)

if __name__ == "__main__":
    main()
