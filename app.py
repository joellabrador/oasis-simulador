import streamlit as st
import pandas as pd

# Configuración de la página web
st.set_page_config(
    page_title="Oasis - Simulador de Sostenibilidad",
    layout="wide"
)

# --- DATOS BASE DEL PROYECTO OASIS ---
CAPACIDAD_NOMINAL = 50000
POBLACION_ABASTECIDA = 200000
CONSUMO_ENERG_M3 = 3.5 
PRECIO_BASE_RED = 0.15 
CAPEX_PLANTA_BASE = 60.0 # Millones de Euros (Obra civil y membranas)

escenarios_data = {
    "Escenario": [
        "1. 100% Red Eléctrica",
        "2. Solo Solar Fotovoltaica",
        "3. Solo Eólica Terrestre",
        "4. Híbrido Terrestre Macro (Elegido)",
        "5. Híbrido Marino Flotante"
    ],
    "CAPEX_Energia_M": [0.0, 4.0, 15.0, 22.0, 28.0],
    "Autoconsumo": [0.0, 0.40, 0.65, 1.00, 1.00],
    "Emisiones_CO2": [35.0, 21.0, 12.2, 0.0, 0.0],
    "Coste_Agua_Amort": [0.78, 0.61, 0.54, 0.45, 0.90],
    "Coste_Agua_Post": [0.78, 0.61, 0.45, 0.25, 0.50]
}
df_escenarios = pd.DataFrame(escenarios_data)

# --- INTERFAZ DE USUARIO ---
st.title("Oasis: Cuadro de Mandos y Simulador de Decisiones")
st.markdown("Herramienta interactiva para evaluar el impacto de las decisiones estratégicas de la planta desalinizadora.")
st.markdown("---")

# BARRA LATERAL 
st.sidebar.header("Configuración y Decisiones")

escenario_seleccionado = st.sidebar.selectbox(
    "Selecciona la Matriz Energética:",
    df_escenarios["Escenario"].tolist(),
    index=3
)

fase = st.sidebar.radio(
    "Fase de la Infraestructura:",
    ["Fase de Amortización (Años 1-15)", "Fase Post-Amortización (> Año 15)"]
)

gestion_salmuera = st.sidebar.selectbox(
    "Gestión de la Salmuera / Residuo:",
    ["Vertido Directo al Mar (Sin gestión)", 
     "Valorización Básica (Solo extracción de NaCl)", 
     "Valorización Avanzada (ZLD Completo - NaCl, Litio y Magnesio)"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("Variables Externas de Mercado")

precio_red_actual = st.sidebar.slider(
    "Precio Mercado de Red Eléctrica (EUR/kWh)", 
    min_value=0.05, 
    max_value=0.50, 
    value=PRECIO_BASE_RED, 
    step=0.01
)

incremento_transporte = st.sidebar.slider(
    "Impacto Costes de Transporte (EUR/m³)", 
    min_value=0.00, 
    max_value=0.15, 
    value=0.00, 
    step=0.01
)

# --- LÓGICA DE CÁLCULO ---
datos_esc = df_escenarios[df_escenarios["Escenario"] == escenario_seleccionado].iloc[0]

capex_energia = datos_esc["CAPEX_Energia_M"]
emisiones = datos_esc["Emisiones_CO2"]
autoconsumo_pct = datos_esc["Autoconsumo"]

# 1. Inversión Inicial (CAPEX Total Real alineado con el PDF)
if gestion_salmuera == "Vertido Directo al Mar (Sin gestión)":
    capex_salmuera = 0.0
elif gestion_salmuera == "Valorización Básica (Solo extracción de NaCl)":
    capex_salmuera = 0.5
elif gestion_salmuera == "Valorización Avanzada (ZLD Completo - NaCl, Litio y Magnesio)":
    capex_salmuera = 3.0

capex_total = CAPEX_PLANTA_BASE + capex_energia + capex_salmuera

# 2. Coste base según fase
if fase == "Fase de Amortización (Años 1-15)":
    coste_agua_base = datos_esc["Coste_Agua_Amort"]
else:
    coste_agua_base = datos_esc["Coste_Agua_Post"]

# 3. Variación de energía de red
dependencia_red = 1.0 - autoconsumo_pct
diferencia_precio_red = precio_red_actual - PRECIO_BASE_RED
impacto_energia = dependencia_red * CONSUMO_ENERG_M3 * diferencia_precio_red

# 4. Impacto económico y ambiental de la salmuera
beneficio_circular = 0.0
texto_salmuera = ""

if gestion_salmuera == "Vertido Directo al Mar (Sin gestión)":
    beneficio_circular = 0.00
    texto_salmuera = "50.000 m³/día vertidos"
elif gestion_salmuera == "Valorización Básica (Solo extracción de NaCl)":
    beneficio_circular = 0.02
    texto_salmuera = "Residuo mitigado parcialmente"
elif gestion_salmuera == "Valorización Avanzada (ZLD Completo - NaCl, Litio y Magnesio)":
    beneficio_circular = 0.05
    texto_salmuera = "0 Litros (Descarga Cero)"

# 5. Cálculo del coste final
coste_agua_final = coste_agua_base + impacto_energia + incremento_transporte - beneficio_circular

# 6. Lógica del Medidor de Reputación (Con puntuación numérica)
puntos_reputacion = 100

if emisiones > 30:
    puntos_reputacion -= 40
elif emisiones > 10:
    puntos_reputacion -= 20

if gestion_salmuera == "Vertido Directo al Mar (Sin gestión)":
    puntos_reputacion -= 40
elif gestion_salmuera == "Valorización Básica (Solo extracción de NaCl)":
    puntos_reputacion -= 15

if puntos_reputacion >= 85:
    reputacion_final = "Excelente"
    color_delta = "normal"      # Se mostrará en Verde
elif puntos_reputacion >= 60:
    reputacion_final = "Buena"
    color_delta = "normal"      # Se mostrará en Verde
elif puntos_reputacion >= 40:
    reputacion_final = "Regular"
    color_delta = "off"         # Se mostrará en Gris
else:
    reputacion_final = "Mala"
    color_delta = "inverse"     # Se mostrará en Rojo


# --- PANTALLA PRINCIPAL ---
st.subheader("Indicadores de Impacto Inmediato")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(label="Coste Final del Agua", value=f"{coste_agua_final:.2f} EUR/m³")

with col2:
    st.metric(label="Inversión Inicial (CAPEX)", value=f"{capex_total:.1f} MEUR")

with col3:
    st.metric(label="Emisiones de CO₂", value=f"{emisiones:.1f} t/día")

with col4:
    st.metric(label="Gestión de Salmuera", value=texto_salmuera)

with col5:
    st.metric(
        label="Reputación Institucional", 
        value=f"{puntos_reputacion} / 100", 
        delta=reputacion_final, 
        delta_color=color_delta
    )

st.markdown("---")

# SECCIONES EXPLICATIVAS (CAPEX Y REPUTACIÓN)
tab1, tab2 = st.tabs(["Análisis de Inversión Inicial (CAPEX)", "Metodología del Cálculo de Reputación"])

with tab1:
    st.markdown("### Desglose de la Inversión Inicial")
    st.markdown(f"La implementación del modelo seleccionado requiere una inversión total de **{capex_total:.1f} millones de euros**, distribuida de la siguiente manera:")
    st.write(f"- **Planta Desalinizadora Base (Obra civil y membranas):** {CAPEX_PLANTA_BASE:.1f} MEUR")
    st.write(f"- **Infraestructura Energética Asociada:** {capex_energia:.1f} MEUR")
    st.write(f"- **Tecnología de Tratamiento de Salmuera:** {capex_salmuera:.1f} MEUR")
    st.markdown("El análisis de viabilidad demuestra que asumir un mayor CAPEX inicial en activos de generación híbrida y sistemas de descarga cero (ZLD) encarece el inicio, pero reduce drásticamente el OPEX a largo plazo y evita estar a merced de las fluctuaciones de la red.")

with tab2:
    st.markdown("### Criterios del Medidor de Reputación")
    st.markdown("La reputación institucional se calcula dinámicamente sobre una base de 100 puntos utilizando indicadores objetivos de impacto ambiental:")
    st.markdown("**1. Penalizaciones por Huella de Carbono:** Alta (>30 t/día) resta 40 puntos. Moderada (10-30 t/día) resta 20 puntos.")
    st.markdown("**2. Penalizaciones por Vertidos al Medio Marino:** Vertido Directo resta 40 puntos. Valorización Básica resta 15 puntos.")

st.markdown("---")

# SECCIÓN VISUAL
st.subheader("Análisis Gráfico")
modo_vista = st.radio(
    "Selecciona el modo de visualización:",
    ["Ver todas las gráficas", "Coste por m³", "Emisiones CO₂", "Inversión Inicial (CAPEX)"],
    horizontal=True
)

df_grafico = df_escenarios.copy()
costes_dinamicos = []
capex_dinamicos = []

for index, row in df_grafico.iterrows():
    # Recalcular el OPEX dinámico
    c_base = row["Coste_Agua_Amort"] if fase == "Fase de Amortización (Años 1-15)" else row["Coste_Agua_Post"]
    dep_red = 1.0 - row["Autoconsumo"]
    imp_energia = dep_red * CONSUMO_ENERG_M3 * (precio_red_actual - PRECIO_BASE_RED)
    coste_dinamico_final = c_base + imp_energia + incremento_transporte - beneficio_circular
    costes_dinamicos.append(coste_dinamico_final)
    
    # Recalcular el CAPEX total dinámico
    c_total = CAPEX_PLANTA_BASE + row["CAPEX_Energia_M"] + capex_salmuera
    capex_dinamicos.append(c_total)

df_grafico["Coste Final (EUR/m³)"] = costes_dinamicos
df_grafico["CAPEX Total (MEUR)"] = capex_dinamicos

if modo_vista == "Ver todas las gráficas":
    col_g1, col_g2, col_g3 = st.columns(3)
    with col_g1:
        st.markdown("**Inversión Inicial Total (M€)**")
        st.bar_chart(data=df_grafico, x="Escenario", y="CAPEX Total (MEUR)", color="#0000ff")
    with col_g2:
        st.markdown("**Coste del Agua Final (€/m³)**")
        st.bar_chart(data=df_grafico, x="Escenario", y="Coste Final (EUR/m³)")
    with col_g3:
        st.markdown("**Emisiones (t CO₂/día)**")
        st.bar_chart(data=df_grafico, x="Escenario", y="Emisiones_CO2", color="#ff4b4b")

elif modo_vista == "Coste por m³":
    st.markdown("**Comparativa Global de Coste Operativo (€/m³)**")
    st.bar_chart(data=df_grafico, x="Escenario", y="Coste Final (EUR/m³)")

elif modo_vista == "Emisiones CO₂":
    st.markdown("**Comparativa de Emisiones (t CO₂/día)**")
    st.bar_chart(data=df_grafico, x="Escenario", y="Emisiones_CO2", color="#ff4b4b")

elif modo_vista == "Inversión Inicial (CAPEX)":
    st.markdown("**Comparativa de Inversión Inicial Total (M€)**")
    st.bar_chart(data=df_grafico, x="Escenario", y="CAPEX Total (MEUR)", color="#0000ff")

st.markdown("---")
st.subheader("Vinculación con los ODS")
st.markdown(f"- ODS 6 (Agua Limpia): Aporte garantizado de {CAPACIDAD_NOMINAL} m³/día.")

if gestion_salmuera == "Vertido Directo al Mar (Sin gestión)":
    st.markdown("- ODS 12 y 14 en Riesgo: El vertido directo amenaza el ecosistema y no se reaprovechan recursos.")
elif gestion_salmuera == "Valorización Básica (Solo extracción de NaCl)":
    st.markdown("- ODS 12 y 14 Parcial: Mitigación básica del impacto marino mediante la recuperación de sal común.")
elif gestion_salmuera == "Valorización Avanzada (ZLD Completo - NaCl, Litio y Magnesio)":
    st.markdown("- ODS 12 y 14: Minería urbana avanzada activada y preservación total del ecosistema marino sin vertidos.")
    
if emisiones == 0:
    st.markdown("- ODS 13 (Acción por el Clima): Balance neto cero de emisiones. Máxima sostenibilidad.")
else:
    st.markdown(f"- ODS 13 Comprometido: Emisión activa de {emisiones} t CO₂ diarias.")