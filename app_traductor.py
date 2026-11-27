"""
=============================================================================
PLATAFORMA EDITORIAL DE TRADUCCIÓN LITERARIA ASISTIDA POR IA (Streamlit)
=============================================================================
Diseño: Equilibrado, moderno, tipografía de alta legibilidad, sin sobrecarga.
Para Traductores Profesionales y Equipos Editoriales.
=============================================================================
"""

import os
import re
import json
import streamlit as st
from agente_traductor import (
    BASE_DIR,
    MemoriaLibro,
    AgenteTraductor,
    SegmentadorTexto,
    obtener_o_pedir_api_key
)
from convertir_a_markdown import convertir_archivo_a_markdown

# -----------------------------------------------------------------------------
# 1. Configuración de Página y Estética Editorial
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Taller de Traducción Editorial (es-CO)",
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
    
    /* Cajas de lectura sobrias */
    .panel-lectura {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1.25rem;
        font-size: 15.5px;
        line-height: 1.7;
        color: #0F172A;
        min-height: 220px;
        white-space: pre-wrap;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
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
    
    /* Indicador de métricas sutil */
    .metrica-chip {
        font-size: 12px;
        background-color: #E2E8F0;
        color: #334155;
        padding: 2px 8px;
        border-radius: 12px;
        font-weight: 500;
    }

    /* Pestañas limpias */
    .stTabs [data-baseweb="tab-list"] {
        gap: 16px;
        border-bottom: 1px solid #E2E8F0;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 15px;
        font-weight: 500;
        padding: 10px 16px;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 2. Inicialización de Motor de IA y Memoria
# -----------------------------------------------------------------------------
@st.cache_resource
def cargar_motor():
    api_key = obtener_o_pedir_api_key()
    memoria = MemoriaLibro()
    agente = AgenteTraductor(api_key, memoria)
    return memoria, agente

memoria, agente = cargar_motor()

# Rutas estándar del proyecto
MD_FUENTE = os.path.join(BASE_DIR, "libro_fuente_ingles.md")
PDF_FUENTE = os.path.join(BASE_DIR, "Confession of Faith for Cumberland Presbyterians 1883.pdf")
ARCHIVO_SALIDA = os.path.join(BASE_DIR, "libro_traducido.md")


def cargar_fragmentos():
    if os.path.exists(MD_FUENTE):
        with open(MD_FUENTE, "r", encoding="utf-8") as f:
            texto = f.read()
        return SegmentadorTexto.dividir_en_fragmentos(texto)
    elif os.path.exists(PDF_FUENTE):
        with st.spinner("Convirtiendo PDF a Markdown con Microsoft MarkItDown..."):
            ruta_md = convertir_archivo_a_markdown(PDF_FUENTE, MD_FUENTE)
            with open(ruta_md, "r", encoding="utf-8") as f:
                texto = f.read()
            return SegmentadorTexto.dividir_en_fragmentos(texto)
    else:
        return [
            "The Cumberland Presbyterian Church was organized in Dickson County, Tennessee, February 4, A.D. 1810."
        ]

if "fragmentos" not in st.session_state:
    st.session_state.fragmentos = cargar_fragmentos()

if "bloque_idx" not in st.session_state:
    st.session_state.bloque_idx = 0

if "resultado_actual" not in st.session_state:
    st.session_state.resultado_actual = None

if "bloque_procesado_id" not in st.session_state:
    st.session_state.bloque_procesado_id = -1


# -----------------------------------------------------------------------------
# 3. Barra Lateral (Progreso, Navegación y Configuración)
# -----------------------------------------------------------------------------
total_bloques = len(st.session_state.fragmentos)
idx_actual = st.session_state.bloque_idx

with st.sidebar:
    st.title("📖 Taller Editorial")
    st.caption("Traducción literaria & teológica | es-CO")
    st.markdown("---")

    # Progreso del libro
    porcentaje = int(((idx_actual + 1) / total_bloques) * 100)
    st.write(f"**Progreso:** Bloque {idx_actual + 1} de {total_bloques} ({porcentaje}%)")
    st.progress((idx_actual + 1) / total_bloques)

    # Navegación rápida entre bloques
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

    # Metadatos del libro activo
    st.markdown("**Obra en Curso**")
    st.markdown(f"**Título:** {memoria.datos.get('titulo', 'Sin título')}")
    st.markdown(f"**Época:** {memoria.datos.get('epoca', '1883')}")
    st.markdown(f"**Norma lingüística:** {memoria.datos.get('dialecto_meta', 'es-CO')}")

    st.markdown("---")

    # Estado del Motor de IA
    st.markdown("**Motor de IA**")
    st.success("🟢 Google Gemini 3.5 Flash (Activo)")
    st.caption("Resiliencia multi-modelo ante alta demanda.")

    st.markdown("---")

    # Descarga directa del libro traducido
    if os.path.exists(ARCHIVO_SALIDA) and os.path.getsize(ARCHIVO_SALIDA) > 0:
        with open(ARCHIVO_SALIDA, "r", encoding="utf-8") as f_out:
            md_traducido = f_out.read()
        st.download_button(
            label="📥 Descargar Traducción (.md)",
            data=md_traducido,
            file_name=f"traduccion_{memoria.datos.get('titulo', 'libro')}.md",
            mime="text/markdown",
            use_container_width=True
        )


# -----------------------------------------------------------------------------
# 4. Área Principal con Pestañas de Trabajo
# -----------------------------------------------------------------------------
pestana_traductor, pestana_lectura, pestana_glosario, pestana_ingesta = st.tabs([
    "✍️ Traducción Bloque a Bloque",
    "📖 Lectura Completa Acumulada",
    "📚 Glosario & Reglas de Estilo",
    "📂 Ingesta de Nuevos Libros (MarkItDown)"
])


# =============================================================================
# PESTAÑA 1: TALLER DE TRADUCCIÓN BLOQUE A BLOQUE
# =============================================================================
with pestana_traductor:
    fragmento_actual = st.session_state.fragmentos[idx_actual]
    palabras_ingles = len(fragmento_actual.split())

    # Inferencia con el agente de IA si cambia el bloque
    if st.session_state.bloque_procesado_id != idx_actual or st.session_state.resultado_actual is None:
        with st.spinner("Analizando teología de 1883 y generando propuesta en español de Colombia..."):
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

    # Cabecera del bloque
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        st.markdown(f"### Bloque #{idx_actual + 1} de {total_bloques}")
    with col_t2:
        st.markdown(f"<div style='text-align: right; padding-top: 8px;'><span class='metrica-chip'>{palabras_ingles} palabras en inglés</span></div>", unsafe_allow_html=True)

    # Vista paralela (Side-by-side)
    col_izq, col_der = st.columns(2, gap="large")

    with col_izq:
        st.markdown(
            f"""<div class="etiqueta-columna">
                <span>Texto Original (Inglés de 1883)</span>
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
                <span>Propuesta Editorial (Español es-CO)</span>
                <span class="metrica-chip">{palabras_esp} palabras ({ratio})</span>
            </div>""",
            unsafe_allow_html=True
        )

        traduccion_editada = st.text_area(
            label="area_traduccion",
            value=traduccion_inicial,
            height=220,
            label_visibility="collapsed",
            help="Puedes editar el texto libremente antes de aprobar."
        )

    # Análisis Filológico y Contexto
    if resultado.get("analisis_epoca"):
        st.markdown(
            f"""<div class="panel-filologia">
                <strong>🧐 Análisis Filológico y Erratas Corregidas:</strong><br>
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

    # Botonera de Acción Human-in-the-Loop
    col_b1, col_b2, col_b3 = st.columns([3, 4, 2])

    with col_b1:
        btn_aprobar = st.button("✓ Aprobar y Avanzar", type="primary", use_container_width=True)

    with col_b2:
        with st.popover("💬 Pedir ajuste en lenguaje natural a la IA"):
            feedback_humano = st.text_input("Instrucción (ej. 'hazlo sonar más formal' o 'usa la palabra X'):")
            if st.button("Re-evaluar con IA") and feedback_humano:
                with st.spinner("Regenerando propuesta con tus indicaciones..."):
                    try:
                        nuevo_resultado = agente.traducir_bloque(fragmento_actual, feedback_traductor=feedback_humano)
                        st.session_state.resultado_actual = nuevo_resultado
                        st.rerun()
                    except Exception as err:
                        st.error(f"Error al reintentar: {err}")

    with col_b3:
        col_ant, col_sig = st.columns(2)
        with col_ant:
            btn_ant = st.button("◀", disabled=(idx_actual == 0), help="Bloque anterior", use_container_width=True)
        with col_sig:
            btn_sig = st.button("▶", disabled=(idx_actual + 1 >= total_bloques), help="Siguiente bloque sin guardar", use_container_width=True)

    # Lógica de Aprobación
    if btn_aprobar:
        texto_final = traduccion_editada.strip()
        if texto_final:
            with open(ARCHIVO_SALIDA, "a", encoding="utf-8") as f_out:
                f_out.write(f"\n\n### Sección {idx_actual + 1}\n\n")
                f_out.write(f"{texto_final}\n")
                if resultado.get("notas_al_pie"):
                    f_out.write("\n")
                    for n in resultado.get("notas_al_pie", []):
                        f_out.write(f"> *[Nota del Traductor sobre '{n.get('referencia')}']*: {n.get('nota')}  \n")

        if idx_actual + 1 < total_bloques:
            st.session_state.bloque_idx += 1
            st.session_state.resultado_actual = None
            st.rerun()
        else:
            st.balloons()
            st.success("🎉 ¡Felicitaciones! Has completado la traducción de toda la obra.")

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

    if os.path.exists(ARCHIVO_SALIDA) and os.path.getsize(ARCHIVO_SALIDA) > 0:
        with open(ARCHIVO_SALIDA, "r", encoding="utf-8") as f_read:
            contenido_acumulado = f_read.read()

        col_l1, col_l2 = st.columns([4, 1])
        with col_l1:
            st.info(f"Palabras traducidas acumuladas: **{len(contenido_acumulado.split()):,} palabras**")
        with col_l2:
            st.download_button(
                label="📥 Exportar .md",
                data=contenido_acumulado,
                file_name=f"traduccion_completa.md",
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
    st.caption("Los términos definidos aquí se inyectan automáticamente en cada consulta a la IA para garantizar consistencia doctrinal.")

    col_g1, col_g2 = st.columns([3, 2], gap="large")

    with col_g1:
        st.markdown("**Términos Vigentes en la Obra:**")
        glosario_items = memoria.datos.get("glosario_terminos", {})
        if glosario_items:
            for k, v in glosario_items.items():
                col_k, col_v, col_del = st.columns([2, 3, 1])
                with col_k:
                    st.write(f"**{k}**")
                with col_v:
                    st.write(f"{v}")
                with col_del:
                    if st.button("🗑️", key=f"del_{k}", help=f"Eliminar {k}"):
                        del memoria.datos["glosario_terminos"][k]
                        memoria.guardar()
                        st.rerun()
        else:
            st.caption("No hay términos registrados en el glosario.")

    with col_g2:
        st.markdown("**Añadir Término Oficial:**")
        with st.form("form_nuevo_termino", clear_on_submit=True):
            nuevo_en = st.text_input("Término en inglés (ej. Covenant of Grace):")
            nuevo_es = st.text_input("Traducción oficial en es-CO (ej. Pacto de Gracia):")
            guardar_btn = st.form_submit_button("Guardar en el Glosario")
            if guardar_btn:
                if nuevo_en and nuevo_es:
                    memoria.agregar_termino(nuevo_en, nuevo_es)
                    st.success(f"Término '{nuevo_en}' registrado.")
                    st.rerun()

        st.markdown("---")
        st.markdown("**Guía de Estilo Activa:**")
        st.info(memoria.datos.get("guia_estilo", "Sin guía configurada."))


# =============================================================================
# PESTAÑA 4: INGESTA DE NUEVOS LIBROS (MARKITDOWN)
# =============================================================================
with pestana_ingesta:
    st.markdown("### 📂 Ingesta de Documentos con Microsoft MarkItDown")
    st.caption("Convierte cualquier libro en PDF o Word (.docx) a Markdown estructurado antes de comenzar la traducción.")

    subida = st.file_uploader("Selecciona o arrastra el archivo de tu libro (PDF o Word)", type=["pdf", "docx"])

    if subida is not None:
        ruta_guardado_temporal = os.path.join(BASE_DIR, subida.name)
        with open(ruta_guardado_temporal, "wb") as f_temp:
            f_temp.write(subida.getbuffer())

        st.success(f"Archivo subido: '{subida.name}' ({subida.size / (1024*1024):.2f} MB)")

        if st.button("🚀 Convertir a Markdown con MarkItDown"):
            with st.spinner("Procesando con Microsoft MarkItDown y normalizando párrafos..."):
                nombre_base = os.path.splitext(subida.name)[0]
                nuevo_md = os.path.join(BASE_DIR, f"{nombre_base}_fuente.md")
                convertir_archivo_a_markdown(ruta_guardado_temporal, nuevo_md)

                with open(nuevo_md, "r", encoding="utf-8") as f_nuevo:
                    texto_nuevo = f_nuevo.read()

                st.session_state.fragmentos = SegmentadorTexto.dividir_en_fragmentos(texto_nuevo)
                st.session_state.bloque_idx = 0
                st.session_state.resultado_actual = None

                st.success(f"¡Conversión completada! El libro fue dividido en {len(st.session_state.fragmentos)} bloques lógicos.")
                st.info("Ya puedes ir a la pestaña '✍️ Traducción Bloque a Bloque' para empezar a traducir.")
