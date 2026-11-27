"""
=============================================================================
PLATAFORMA EDITORIAL DE TRADUCCIÓN LITERARIA ASISTIDA POR IA (Streamlit)
=============================================================================
Diseño: Equilibrado, moderno, alta legibilidad, soporte para cualquier libro (PDF/Word/MD/TXT),
persistencia de progreso en disco y nube (exportar/importar proyecto .json),
y reconocimiento automático del bloque donde quedó el traductor.
=============================================================================
"""

import os
import re
import json
import time
from datetime import datetime
import streamlit as st
from agente_traductor import (
    BASE_DIR,
    MemoriaLibro,
    AgenteTraductor,
    SegmentadorTexto,
    obtener_o_pedir_api_key
)
from convertir_a_markdown import (
    extraer_texto_de_archivo_o_buffer,
    limpiar_texto_literario
)

# -----------------------------------------------------------------------------
# 1. Configuración de Página y Estética Editorial
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Taller de Traducción Editorial",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS de alta calidad editorial: tonos pizarra, bordes sutiles, espaciado cómodo
st.markdown("""
<style>
    /* Estructura general */
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2.5rem;
        max-width: 1280px;
    }
    
    /* Cajas de lectura sobrias y perfectamente simétricas */
    .panel-lectura {
        background-color: #F8FAFC;
        border: 1px solid #CBD5E1;
        border-radius: 8px;
        padding: 1.15rem;
        font-size: 17.5px;
        line-height: 1.75;
        color: #0F172A;
        height: 310px;
        min-height: 310px;
        max-height: 310px;
        overflow-y: auto;
        white-space: pre-wrap;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
        box-sizing: border-box;
    }

    /* Caja editable derecha: misma altura, misma fuente, misma separación */
    textarea[aria-label="area_traduccion"] {
        font-size: 17.5px !important;
        line-height: 1.75 !important;
        color: #0F172A !important;
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
        padding: 1.15rem !important;
        height: 310px !important;
        min-height: 310px !important;
        max-height: 310px !important;
        box-sizing: border-box !important;
    }

    /* Barras de desplazamiento sutiles y elegantes */
    .panel-lectura::-webkit-scrollbar,
    textarea[aria-label="area_traduccion"]::-webkit-scrollbar {
        width: 7px;
    }
    .panel-lectura::-webkit-scrollbar-thumb,
    textarea[aria-label="area_traduccion"]::-webkit-scrollbar-thumb {
        background: #CBD5E1;
        border-radius: 4px;
    }
    
    .etiqueta-columna {
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.8px;
        color: #64748B;
        text-transform: uppercase;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    /* Caja de análisis filológico */
    .panel-filologia {
        background-color: #F1F5F9;
        border-left: 4px solid #3B82F6;
        padding: 0.9rem 1.1rem;
        font-size: 14px;
        line-height: 1.55;
        color: #1E293B;
        border-radius: 0 6px 6px 0;
        margin-top: 1rem;
        margin-bottom: 1.2rem;
    }
    
    /* Chips métricos */
    .metrica-chip {
        display: inline-block;
        background-color: #E2E8F0;
        color: #334155;
        font-size: 11.5px;
        font-weight: 600;
        padding: 2px 9px;
        border-radius: 12px;
    }
    
    .metrica-chip-verde {
        display: inline-block;
        background-color: #DCFCE7;
        color: #166534;
        font-size: 11.5px;
        font-weight: 600;
        padding: 2px 9px;
        border-radius: 12px;
    }

    /* Tarjetas de bienvenida y selección */
    .tarjeta-bienvenida {
        background: linear-gradient(180deg, #F8FAFC 0%, #FFFFFF 100%);
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 1.8rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 2. Persistencia y Gestión del Proyecto
# -----------------------------------------------------------------------------
ARCHIVO_PROGRESO_LOCAL = os.path.join(BASE_DIR, "progreso_traduccion.json")

def guardar_proyecto_en_disco(proyecto: dict):
    """Guarda el estado completo del proyecto en progreso_traduccion.json."""
    if not proyecto:
        return
    proyecto["fecha_actualizacion"] = datetime.now().isoformat()
    try:
        with open(ARCHIVO_PROGRESO_LOCAL, "w", encoding="utf-8") as f:
            json.dump(proyecto, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.warning(f"No se pudo autoguardar en disco local: {e}")

def cargar_proyecto_desde_disco() -> dict:
    """Carga el proyecto guardado en disco si existe y es válido."""
    if os.path.exists(ARCHIVO_PROGRESO_LOCAL):
        try:
            with open(ARCHIVO_PROGRESO_LOCAL, "r", encoding="utf-8") as f:
                datos = json.load(f)
                if isinstance(datos, dict) and "fragmentos" in datos and len(datos["fragmentos"]) > 0:
                    return datos
        except Exception:
            return None
    return None

def compilar_libro_traducido(proyecto: dict) -> str:
    """Compila todos los bloques traducidos en un documento Markdown fluido y ordenado."""
    titulo = proyecto.get("titulo", "Libro Traducido")
    autor = proyecto.get("autor", "Autor Desconocido")
    epoca = proyecto.get("epoca", "No especificada")
    dialecto = proyecto.get("dialecto_meta", "Español de Colombia (es-CO)")
    
    lineas = [
        f"# {titulo}",
        f"**Autor:** {autor} | **Época/Contexto:** {epoca}",
        f"**Norma lingüística:** {dialecto}",
        f"**Compilado:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "\n---\n"
    ]
    
    traducciones = proyecto.get("traducciones", {})
    fragmentos = proyecto.get("fragmentos", [])
    
    bloques_agregados = 0
    for i in range(len(fragmentos)):
        k = str(i)
        if k in traducciones:
            item = traducciones[k]
            texto_trad = item.get("traduccion", "").strip()
            if texto_trad:
                bloques_agregados += 1
                lineas.append(f"### Sección {i + 1}\n")
                lineas.append(texto_trad)
                lineas.append("")
                
                notas = item.get("notas_al_pie", [])
                if notas:
                    for n in notas:
                        ref = n.get("referencia", "").strip()
                        nota = n.get("nota", "").strip()
                        if ref or nota:
                            lineas.append(f"> *[Nota del Traductor sobre '{ref}']*: {nota}  ")
                    lineas.append("")
                    
    if bloques_agregados == 0:
        return ""
    return "\n".join(lineas)


# -----------------------------------------------------------------------------
# 3. Inicialización del Motor de IA y Clave API
# -----------------------------------------------------------------------------
if "custom_api_key" not in st.session_state:
    st.session_state.custom_api_key = ""

api_key = obtener_o_pedir_api_key() or st.session_state.custom_api_key

@st.cache_resource
def obtener_motor(clave: str):
    if not clave:
        return None, None
    try:
        mem = MemoriaLibro()
        agt = AgenteTraductor(clave, mem)
        return mem, agt
    except Exception as e:
        return None, str(e)

memoria = None
agente = None

if api_key:
    _mem, _agt = obtener_motor(api_key)
    if _mem is not None:
        memoria = _mem
        agente = _agt
    else:
        st.error(f"Error al inicializar cliente Gemini: {_agt}")


# -----------------------------------------------------------------------------
# 4. Estado de Sesión del Proyecto
# -----------------------------------------------------------------------------
if "proyecto" not in st.session_state:
    # Intentar restaurar automáticamente desde el disco local
    proyecto_guardado = cargar_proyecto_desde_disco()
    if proyecto_guardado:
        st.session_state.proyecto = proyecto_guardado
        st.session_state.bloque_idx = proyecto_guardado.get("bloque_actual_idx", 0)
    else:
        st.session_state.proyecto = None

if "bloque_idx" not in st.session_state:
    st.session_state.bloque_idx = 0

if "resultado_actual" not in st.session_state:
    st.session_state.resultado_actual = None

if "bloque_procesado_id" not in st.session_state:
    st.session_state.bloque_procesado_id = -1


# -----------------------------------------------------------------------------
# 5. Si no hay Clave API configurada, solicitarla amigablemente
# -----------------------------------------------------------------------------
if not agente:
    st.markdown("## 🔑 Conexión al Motor de Inteligencia Artificial")
    st.info("""
    Para traducir libros con rigor filológico y estilo literario colombiano, el taller necesita conectarse con Google Gemini.
    Puedes crear una clave API gratuita en menos de 1 minuto en [Google AI Studio](https://aistudio.google.com/app/apikey).
    """)
    
    with st.form("form_clave_api"):
        clave_ingresada = st.text_input("Ingresa o pega tu Gemini API Key:", type="password", placeholder="AIzaSy...")
        btn_clave = st.form_submit_button("Conectar y Continuar", type="primary")
        if btn_clave and clave_ingresada:
            st.session_state.custom_api_key = clave_ingresada.strip()
            # Guardar también en clave_api.txt para mayor comodidad local
            try:
                with open(os.path.join(BASE_DIR, "clave_api.txt"), "w", encoding="utf-8") as f_k:
                    f_k.write(clave_ingresada.strip())
            except Exception:
                pass
            st.success("¡Clave guardada con éxito!")
            st.rerun()
    st.stop()


# -----------------------------------------------------------------------------
# 6. Pantalla de Bienvenida y Selección de Libro (Si no hay proyecto activo)
# -----------------------------------------------------------------------------
if st.session_state.proyecto is None:
    st.title("📖 Taller de Traducción Editorial Asistida por IA")
    st.caption("Localización literaria y teológica de alta fidelidad | Español de Colombia (es-CO)")
    st.markdown("---")

    # Si hay un archivo guardado en el servidor/disco pero el usuario no lo tiene cargado
    proyecto_en_disco = cargar_proyecto_desde_disco()
    if proyecto_en_disco:
        tit = proyecto_en_disco.get("titulo", "Obra anterior")
        tot = len(proyecto_en_disco.get("fragmentos", []))
        trad = len(proyecto_en_disco.get("traducciones", {}))
        pct = int((trad / max(1, tot)) * 100)
        ult_idx = proyecto_en_disco.get("bloque_actual_idx", 0)

        st.markdown(f"""
        <div class="tarjeta-bienvenida">
            <h3 style="margin-top: 0; color: #1E293B;">📌 Proyecto en curso detectado</h3>
            <p style="font-size: 16px; margin-bottom: 8px;">
                <strong>Obra:</strong> <em>{tit}</em> &nbsp;|&nbsp; 
                <strong>Progreso:</strong> {trad} de {tot} bloques traducidos (<strong>{pct}%</strong>)
            </p>
            <p style="color: #64748B; font-size: 14px; margin-bottom: 16px;">
                Última sección activa: Bloque #{ult_idx + 1}. Puedes continuar exactamente donde quedaste.
            </p>
        </div>
        """, unsafe_allow_html=True)

        col_cont, col_desc = st.columns([2, 5])
        with col_cont:
            if st.button("▶ Continuar este Proyecto", type="primary", use_container_width=True):
                st.session_state.proyecto = proyecto_en_disco
                st.session_state.bloque_idx = ult_idx
                st.session_state.resultado_actual = None
                st.rerun()
        with col_desc:
            st.caption("O inicia un libro diferente o carga otro archivo de respaldo más abajo.")

        st.markdown("<br>", unsafe_allow_html=True)

    # Opciones para iniciar libro nuevo o cargar respaldo
    tab_nuevo, tab_respaldo = st.tabs([
        "📤 Subir un Libro Nuevo (PDF, Word, Markdown, Texto)",
        "💾 Cargar Respaldo de Progreso (.json)"
    ])

    with tab_nuevo:
        st.markdown("#### Sube el libro que deseas traducir")
        st.write("Acepta archivos **PDF**, **Word (.docx)**, **Markdown (.md)** o **Texto plano (.txt)**. Microsoft MarkItDown extraerá el texto y limpiará los saltos de imprenta automáticamente.")

        archivo_subido = st.file_uploader(
            "Selecciona o arrastra el archivo de tu libro:",
            type=["pdf", "docx", "md", "txt"],
            help="Sube el archivo original que tu equipo va a traducir."
        )

        if archivo_subido:
            nombre_sugerido = os.path.splitext(archivo_subido.name)[0].replace("_", " ").title()
            
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                titulo_obra = st.text_input("Título de la obra:", value=nombre_sugerido)
                autor_obra = st.text_input("Autor o entidad eclesiástica/editorial:", value="Autor por definir")
            with col_f2:
                epoca_obra = st.text_input("Época, año o género histórico:", value="Siglo XIX / Teológico / Literario")
                dialecto_meta = st.text_input("Norma lingüística meta:", value="Español de Colombia (es-CO) culto y literario")

            guia_estilo = st.text_area(
                "Guía de estilo y tono para el agente:",
                value="Tratamiento solemne, respetuoso y fiel al original. Sintaxis fluida, elocuente y elegante en español de Colombia culto, sin modismos anacrónicos.",
                height=90
            )

            if st.button("🚀 Iniciar Proyecto y Segmentar Libro", type="primary", use_container_width=True):
                with st.spinner("Extrayendo contenido con Microsoft MarkItDown y segmentando párrafos..."):
                    try:
                        texto_limpio = extraer_texto_de_archivo_o_buffer(archivo_subido, archivo_subido.name)
                        if not texto_limpio.strip():
                            st.error("No se pudo extraer texto del archivo subido. Verifica que no sea un escaneo vacío.")
                            st.stop()

                        fragmentos = SegmentadorTexto.dividir_en_fragmentos(texto_limpio, max_palabras=220)
                        if not fragmentos:
                            st.error("El texto extraído no contiene suficientes párrafos legibles.")
                            st.stop()

                        nuevo_proyecto = {
                            "version": "2.0",
                            "titulo": titulo_obra.strip() or nombre_sugerido,
                            "autor": autor_obra.strip() or "Autor",
                            "epoca": epoca_obra.strip() or "General",
                            "dialecto_meta": dialecto_meta.strip() or "Español de Colombia (es-CO)",
                            "guia_estilo": guia_estilo.strip(),
                            "glosario_terminos": {},
                            "fragmentos": fragmentos,
                            "traducciones": {},
                            "bloque_actual_idx": 0,
                            "fecha_creacion": datetime.now().isoformat(),
                            "fecha_actualizacion": datetime.now().isoformat()
                        }

                        guardar_proyecto_en_disco(nuevo_proyecto)
                        st.session_state.proyecto = nuevo_proyecto
                        st.session_state.bloque_idx = 0
                        st.session_state.resultado_actual = None
                        st.success(f"¡Libro cargado con éxito! Se crearon {len(fragmentos)} bloques lógicos.")
                        st.rerun()

                    except Exception as err:
                        st.error(f"Error al procesar el libro: {err}")

    with tab_respaldo:
        st.markdown("#### Cargar progreso desde un archivo .json")
        st.write("Si tú o un compañero ya avanzaron en la traducción en otro computador o en la nube y descargaron su archivo de progreso, súbelo aquí para continuar exactamente en la misma sección:")

        archivo_json = st.file_uploader(
            "Selecciona tu archivo de progreso (.json):",
            type=["json"],
            key="uploader_json_progreso"
        )

        if archivo_json:
            try:
                contenido_json = json.loads(archivo_json.getvalue().decode("utf-8"))
                if "fragmentos" in contenido_json and len(contenido_json["fragmentos"]) > 0:
                    tit = contenido_json.get("titulo", "Obra")
                    tot = len(contenido_json["fragmentos"])
                    trad = len(contenido_json.get("traducciones", {}))
                    idx_restaurado = contenido_json.get("bloque_actual_idx", 0)

                    st.success(f"Archivo válido detectado: **{tit}** ({trad} de {tot} bloques traducidos).")
                    if st.button("📥 Restaurar y Continuar Traducción", type="primary", use_container_width=True):
                        guardar_proyecto_en_disco(contenido_json)
                        st.session_state.proyecto = contenido_json
                        st.session_state.bloque_idx = idx_restaurado
                        st.session_state.resultado_actual = None
                        st.rerun()
                else:
                    st.error("El archivo JSON no contiene la estructura requerida de fragmentos de traducción.")
            except Exception as e:
                st.error(f"Error al leer el archivo JSON: {e}")

    st.stop()


# -----------------------------------------------------------------------------
# 7. Espacio de Trabajo Activo (Proyecto Cargado)
# -----------------------------------------------------------------------------
proyecto = st.session_state.proyecto
fragmentos = proyecto.get("fragmentos", [])
traducciones = proyecto.get("traducciones", {})
total_bloques = len(fragmentos)

# Validar que el índice no supere los límites
idx_actual = max(0, min(st.session_state.bloque_idx, total_bloques - 1))
st.session_state.bloque_idx = idx_actual

# Sincronizar memoria del libro para que el agente conozca el contexto dinámico
memoria.actualizar_desde_proyecto(proyecto)


# -----------------------------------------------------------------------------
# 8. Barra Lateral (Progreso, Navegación y Respaldos)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("📖 Taller Editorial")
    st.caption("Traducción literaria & teológica | es-CO")
    st.markdown("---")

    # Datos de la obra activa
    st.markdown(f"**Obra:** {proyecto.get('titulo', 'Sin título')}")
    st.markdown(f"**Autor:** {proyecto.get('autor', 'No especificado')}")
    st.markdown(f"**Época:** {proyecto.get('epoca', 'Histórica')}")

    st.markdown("---")

    # Métrica de progreso
    total_traducidos = len(traducciones)
    porcentaje = int((total_traducidos / max(1, total_bloques)) * 100)
    st.write(f"**Progreso:** {total_traducidos} de {total_bloques} bloques traducidos ({porcentaje}%)")
    st.progress(total_traducidos / max(1, total_bloques))
    st.write(f"**Sección actual:** Bloque #{idx_actual + 1}")

    # Salto directo a bloque
    col_nav1, col_nav2 = st.columns([2, 1])
    with col_nav1:
        nuevo_idx = st.number_input(
            "Ir al bloque:",
            min_value=1,
            max_value=total_bloques,
            value=idx_actual + 1,
            step=1
        ) - 1
    with col_nav2:
        st.write("")
        st.write("")
        if st.button("Saltar", use_container_width=True):
            if nuevo_idx != idx_actual:
                st.session_state.bloque_idx = nuevo_idx
                st.session_state.resultado_actual = None
                st.rerun()

    st.markdown("---")

    # GUARDAR / DESCARGAR EN LA NUBE O EN CUALQUIER MÁQUINA
    st.markdown("**💾 Guardar y Respaldar en la Nube**")
    st.caption("Descarga este archivo para continuar en cualquier computador o cuando Streamlit Cloud se reinicie:")

    json_respaldo = json.dumps(proyecto, ensure_ascii=False, indent=2)
    nombre_archivo_json = f"progreso_{re.sub(r'[^a-zA-Z0-9]+', '_', proyecto.get('titulo', 'libro')).lower()}.json"
    
    st.download_button(
        label="💾 Descargar Respaldo (.json)",
        data=json_respaldo,
        file_name=nombre_archivo_json,
        mime="application/json",
        use_container_width=True,
        help="Guarda tu archivo de avance para no perder nada."
    )

    # Descarga de la traducción acumulada en Markdown
    md_traducido_actual = compilar_libro_traducido(proyecto)
    if md_traducido_actual:
        nombre_archivo_md = f"traduccion_{re.sub(r'[^a-zA-Z0-9]+', '_', proyecto.get('titulo', 'libro')).lower()}.md"
        st.download_button(
            label="📄 Descargar Traducción (.md)",
            data=md_traducido_actual,
            file_name=nombre_archivo_md,
            mime="text/markdown",
            use_container_width=True,
            help="Descarga el texto traducido y aprobado hasta este momento."
        )

    st.markdown("---")

    # Opción de cambiar de libro
    if st.button("🔄 Cambiar de Libro / Salir", use_container_width=True):
        guardar_proyecto_en_disco(proyecto)
        st.session_state.proyecto = None
        st.session_state.resultado_actual = None
        st.rerun()


# -----------------------------------------------------------------------------
# 9. Área Principal de Trabajo (Pestañas)
# -----------------------------------------------------------------------------
pestana_traductor, pestana_lectura, pestana_glosario, pestana_proyecto = st.tabs([
    "✍️ Traducción Bloque a Bloque",
    "📖 Lectura Completa Acumulada",
    "📚 Glosario & Reglas de Estilo",
    "💾 Estado del Proyecto y Exportación"
])


# =============================================================================
# PESTAÑA 1: TALLER DE TRADUCCIÓN BLOQUE A BLOQUE
# =============================================================================
with pestana_traductor:
    fragmento_actual = fragmentos[idx_actual]
    palabras_ingles = len(fragmento_actual.split())
    clave_bloque = str(idx_actual)
    ya_traducido = clave_bloque in traducciones

    # Inferencia con IA solo si no se ha cargado propuesta para este bloque
    if ya_traducido:
        # Ya fue aprobado anteriormente por el traductor humano
        datos_guardados = traducciones[clave_bloque]
        resultado = {
            "traduccion_es_co": datos_guardados.get("traduccion", ""),
            "analisis_epoca": datos_guardados.get("analisis_epoca", "Sección previamente aprobada."),
            "decisiones_clave": datos_guardados.get("decisiones_clave", []),
            "notas_al_pie": datos_guardados.get("notas_al_pie", [])
        }
        st.session_state.resultado_actual = resultado
        st.session_state.bloque_procesado_id = idx_actual
    else:
        # Bloque nuevo pendiente de traducción
        if st.session_state.bloque_procesado_id != idx_actual or st.session_state.resultado_actual is None:
            with st.spinner("Generando propuesta editorial rigurosa en español de Colombia con Gemini..."):
                try:
                    res = agente.traducir_bloque(fragmento_actual)
                    st.session_state.resultado_actual = res
                    st.session_state.bloque_procesado_id = idx_actual
                except Exception as e:
                    st.error(f"Error de conexión con la IA: {e}")
                    st.session_state.resultado_actual = {
                        "analisis_epoca": "Error al conectar con la API de IA.",
                        "traduccion_es_co": "",
                        "decisiones_clave": [],
                        "notas_al_pie": []
                    }
        resultado = st.session_state.resultado_actual

    # Cabecera de la sección
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        st.markdown(f"### Bloque #{idx_actual + 1} de {total_bloques}")
    with col_t2:
        badge_estado = (
            "<span class='metrica-chip-verde'>✓ Aprobado y Guardado</span>" 
            if ya_traducido else 
            "<span class='metrica-chip'>⏳ Pendiente de Aprobación</span>"
        )
        st.markdown(f"<div style='text-align: right; padding-top: 8px;'>{badge_estado} &nbsp; <span class='metrica-chip'>{palabras_ingles} palabras en inglés</span></div>", unsafe_allow_html=True)

    # Vista paralela (Side-by-side)
    col_izq, col_der = st.columns(2, gap="large")

    with col_izq:
        st.markdown(
            f"""<div class="etiqueta-columna">
                <span>Texto Original ({proyecto.get('epoca', 'Inglés')})</span>
                <span class="metrica-chip">Fuente</span>
            </div>""",
            unsafe_allow_html=True
        )
        st.markdown(f'<div class="panel-lectura">{fragmento_actual}</div>', unsafe_allow_html=True)

    with col_der:
        traduccion_inicial = resultado.get("traduccion_es_co", "")
        palabras_esp = len(traduccion_inicial.split())
        ratio = f"{((palabras_esp - palabras_ingles) / max(1, palabras_ingles)) * 100:+.0f}%"

        st.markdown(
            f"""<div class="etiqueta-columna">
                <span>Propuesta Editorial ({proyecto.get('dialecto_meta', 'es-CO')})</span>
                <span class="metrica-chip">{palabras_esp} palabras ({ratio})</span>
            </div>""",
            unsafe_allow_html=True
        )

        traduccion_editada = st.text_area(
            label="area_traduccion",
            value=traduccion_inicial,
            height=310,
            label_visibility="collapsed",
            help="Edita el texto libremente antes de aprobar."
        )

    # Análisis Filológico y Contexto
    if resultado.get("analisis_epoca"):
        st.markdown(
            f"""<div class="panel-filologia">
                <strong>🧠 Análisis Filológico y Erratas Corregidas:</strong><br>
                {resultado.get("analisis_epoca")}
            </div>""",
            unsafe_allow_html=True
        )

    # Desplegables de Decisiones Léxicas y Notas al Pie
    col_exp1, col_exp2 = st.columns(2, gap="large")

    with col_exp1:
        with st.expander("📋 Decisiones de Traducción y Justificación", expanded=False):
            decisiones = resultado.get("decisiones_clave", [])
            if decisiones:
                for d in decisiones:
                    st.markdown(f"• **{d.get('termino_original')}** ➔ *{d.get('traduccion_elegida')}*  \n_{d.get('justificacion')}_")
            else:
                st.caption("No se requirieron decisiones léxicas complejas en este bloque.")

    with col_exp2:
        with st.expander("📌 Notas al Pie Sugeridas para el Lector", expanded=False):
            notas = resultado.get("notas_al_pie", [])
            if notas:
                for n in notas:
                    st.markdown(f"• **[{n.get('referencia')}]:** {n.get('nota')}")
            else:
                st.caption("No se sugieren notas al pie adicionales.")

    st.markdown("<br>", unsafe_allow_html=True)

    # Botonera de Acción
    col_b1, col_b2, col_b3 = st.columns([3, 4, 2])

    with col_b1:
        btn_aprobar = st.button("✓ Aprobar y Avanzar", type="primary", use_container_width=True)

    with col_b2:
        with st.popover("💬 Pedir ajuste en lenguaje natural a la IA"):
            feedback_humano = st.text_input("Instrucción (ej. 'hazlo sonar más solemne' o 'usa el término X'):")
            if st.button("Re-evaluar con IA") and feedback_humano:
                with st.spinner("Regenerando propuesta con tus indicaciones..."):
                    try:
                        nuevo_res = agente.traducir_bloque(fragmento_actual, feedback_traductor=feedback_humano)
                        st.session_state.resultado_actual = nuevo_res
                        st.rerun()
                    except Exception as err:
                        st.error(f"Error al reintentar: {err}")

    with col_b3:
        col_ant, col_sig = st.columns(2)
        with col_ant:
            btn_ant = st.button("◀", disabled=(idx_actual == 0), help="Bloque anterior", use_container_width=True)
        with col_sig:
            btn_sig = st.button("▶", disabled=(idx_actual + 1 >= total_bloques), help="Siguiente bloque", use_container_width=True)

    # Guardar aprobación
    if btn_aprobar:
        texto_final = traduccion_editada.strip()
        if texto_final:
            traducciones[clave_bloque] = {
                "traduccion": texto_final,
                "analisis_epoca": resultado.get("analisis_epoca", ""),
                "decisiones_clave": resultado.get("decisiones_clave", []),
                "notas_al_pie": resultado.get("notas_al_pie", [])
            }
            proyecto["traducciones"] = traducciones
            # Actualizar el bloque donde quedó el usuario para retomar desde aquí
            if idx_actual + 1 < total_bloques:
                proyecto["bloque_actual_idx"] = idx_actual + 1
                st.session_state.bloque_idx = idx_actual + 1
            else:
                proyecto["bloque_actual_idx"] = idx_actual

            # Autoguardado inmediato en disco
            guardar_proyecto_en_disco(proyecto)
            st.session_state.resultado_actual = None

            if idx_actual + 1 >= total_bloques:
                st.balloons()
                st.success("🎉 ¡Felicitaciones! Has completado la traducción de toda la obra.")
            st.rerun()

    if btn_ant and idx_actual > 0:
        st.session_state.bloque_idx -= 1
        st.session_state.resultado_actual = None
        st.rerun()

    if btn_sig and idx_actual + 1 < total_bloques:
        st.session_state.bloque_idx += 1
        st.session_state.resultado_actual = None
        st.rerun()


# =============================================================================
# PESTAÑA 2: LECTURA COMPLETA ACUMULADA
# =============================================================================
with pestana_lectura:
    st.markdown("### 📖 Lectura Continua de la Traducción")
    st.caption("Visualiza el texto acumulado tal como lo leerá el público, evaluando ritmo, cohesión y fluidez.")

    contenido_acumulado = compilar_libro_traducido(proyecto)

    if contenido_acumulado:
        col_l1, col_l2 = st.columns([4, 1])
        with col_l1:
            total_palabras_es = len(contenido_acumulado.split())
            st.info(f"Palabras traducidas acumuladas: **{total_palabras_es:,} palabras** en **{len(traducciones)} de {total_bloques} bloques**.")
        with col_l2:
            st.download_button(
                label="📥 Exportar .md",
                data=contenido_acumulado,
                file_name=f"traduccion_{re.sub(r'[^a-zA-Z0-9]+', '_', proyecto.get('titulo', 'libro')).lower()}.md",
                mime="text/markdown",
                use_container_width=True
            )

        st.markdown("---")
        st.markdown(contenido_acumulado)
    else:
        st.info("Aún no has aprobado ningún bloque. Comienza a aprobar bloques en la pestaña 'Traducción' para ver el libro aquí.")


# =============================================================================
# PESTAÑA 3: GLOSARIO Y REGLAS DE ESTILO
# =============================================================================
with pestana_glosario:
    st.markdown("### 📚 Glosario Editorial Permanente")
    st.caption("Los términos definidos aquí se inyectan automáticamente en cada consulta a la IA para garantizar consistencia terminológica en todo el libro.")

    glosario_items = proyecto.get("glosario_terminos", {})

    col_g1, col_g2 = st.columns([3, 2], gap="large")

    with col_g1:
        st.markdown("**Términos Vigentes en esta Obra:**")
        if glosario_items:
            for k, v in list(glosario_items.items()):
                col_k, col_v, col_del = st.columns([2, 3, 1])
                with col_k:
                    st.write(f"**{k}**")
                with col_v:
                    st.write(f"{v}")
                with col_del:
                    if st.button("🗑️", key=f"del_{k}", help=f"Eliminar {k}"):
                        del proyecto["glosario_terminos"][k]
                        guardar_proyecto_en_disco(proyecto)
                        memoria.actualizar_desde_proyecto(proyecto)
                        st.rerun()
        else:
            st.caption("No hay términos registrados en el glosario de este libro aún.")

    with col_g2:
        st.markdown("**Añadir Término Oficial:**")
        with st.form("form_nuevo_termino", clear_on_submit=True):
            nuevo_en = st.text_input("Término en inglés (ej. Covenant of Grace):")
            nuevo_es = st.text_input("Traducción oficial en es-CO (ej. Pacto de Gracia):")
            guardar_btn = st.form_submit_button("Guardar en el Glosario")
            if guardar_btn and nuevo_en and nuevo_es:
                proyecto.setdefault("glosario_terminos", {})[nuevo_en.strip().lower()] = nuevo_es.strip()
                guardar_proyecto_en_disco(proyecto)
                memoria.actualizar_desde_proyecto(proyecto)
                st.success(f"Término '{nuevo_en}' registrado.")
                st.rerun()

        st.markdown("---")
        st.markdown("**Guía de Estilo Activa:**")
        st.info(proyecto.get("guia_estilo", "Sin guía configurada."))


# =============================================================================
# PESTAÑA 4: ESTADO DEL PROYECTO Y EXPORTACIÓN
# =============================================================================
with pestana_proyecto:
    st.markdown("### 💾 Resumen del Proyecto y Gestión de Respaldos")
    st.caption("Verifica el avance, descarga copias de seguridad portátiles o exporta la obra completa.")

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("Total Bloques", total_bloques)
    with col_m2:
        st.metric("Traducidos", len(traducciones))
    with col_m3:
        st.metric("Pendientes", total_bloques - len(traducciones))
    with col_m4:
        st.metric("Progreso", f"{porcentaje}%")

    st.markdown("---")

    col_e1, col_e2 = st.columns(2)
    with col_e1:
        st.markdown("#### 1. Archivo de Progreso Portátil (.json)")
        st.write("Guarda este archivo en tu computador o envíaselo a tus compañeros. Cualquiera puede cargarlo en Streamlit Cloud y continuar exactamente en el mismo bloque con todas las traducciones intactas.")
        st.download_button(
            label="💾 Descargar Respaldo del Proyecto (.json)",
            data=json_respaldo,
            file_name=nombre_archivo_json,
            mime="application/json",
            type="primary",
            use_container_width=True
        )

    with col_e2:
        st.markdown("#### 2. Libro Traducido Completo (.md)")
        st.write("Descarga el manuscrito en Markdown listo para edición, publicación, diagramación o impresión.")
        if md_traducido_actual:
            st.download_button(
                label="📄 Descargar Manuscrito en Markdown (.md)",
                data=md_traducido_actual,
                file_name=f"traduccion_{re.sub(r'[^a-zA-Z0-9]+', '_', proyecto.get('titulo', 'libro')).lower()}.md",
                mime="text/markdown",
                use_container_width=True
            )
        else:
            st.info("Aprueba al menos un bloque para generar la descarga del manuscrito.")

    st.markdown("---")
    st.markdown("#### ⚠️ Cambiar de Libro o Iniciar Nuevo Proyecto")
    st.write("Si deseas traducir otro libro, puedes cerrar la sesión de este libro. Tu avance quedará guardado automáticamente en el servidor y también puedes descargar el archivo `.json` de arriba por seguridad.")
    
    if st.button("📁 Cerrar este Proyecto y Abrir Otro Libro", type="secondary"):
        guardar_proyecto_en_disco(proyecto)
        st.session_state.proyecto = None
        st.session_state.resultado_actual = None
        st.rerun()
