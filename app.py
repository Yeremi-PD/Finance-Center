import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import base64
import streamlit.components.v1 as components
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CONFIGURACIÓN ---
from PIL import Image, ImageOps

# Abrimos la imagen asegurando que lea el fondo transparente (RGBA)
logo_raw = Image.open("logo.png").convert("RGBA")

# 1. Recortar TODO el espacio transparente inútil de los bordes
caja_del_logo = logo_raw.getbbox()
if caja_del_logo:
    logo_recortado = logo_raw.crop(caja_del_logo)
else:
    logo_recortado = logo_raw

# 2. Ahora sí, lo volvemos un cuadrado perfecto basado SOLO en el logo
tamaño_max = max(logo_recortado.size)
logo_final = ImageOps.pad(logo_recortado, (tamaño_max, tamaño_max))

st.set_page_config(page_title="Financial Center", page_icon=logo_final, layout="wide")
st.logo("logo.png")

# Ocultar marca de agua, ajustar espacio y ESTILIZAR UI (Botones, Inputs, Tarjetas y TABLAS)
st.markdown("""
<style>
    /* Ocultar elementos por defecto de Streamlit */
    #MainMenu {visibility: hidden;} 
    footer {visibility: hidden;} 
    header {visibility: hidden;}
    
    /* Ocultar el indicador de "Running..." arriba a la derecha para evitar parpadeos visuales */
    [data-testid="stStatusWidget"] {visibility: hidden;}
    
    /* Ajustar el contenedor principal */
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 1rem !important;
        margin-top: -80px !important; /* Sube todo al límite máximo */
    }

    /* 🌟 MAGIA PARA LOS BOTONES 🌟 */
    div[data-testid="stButton"] > button {
        border-radius: 10px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2) !important;
        transition: all 0.3s ease !important;
    }
    
    div[data-testid="stButton"] > button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 15px rgba(76, 175, 80, 0.3) !important;
        border-color: #4CAF50 !important;
    }

    div[data-testid="stButton"] > button:active {
        transform: translateY(1px) !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2) !important;
    }

    /* 🌟 ESTILIZAR LOS INPUTS Y SELECTBOX 🌟 */
    div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {
        border-radius: 8px !important;
        border: 1px solid rgba(255,255,255, 0.1) !important;
        background-color: rgba(25, 25, 25, 0.8) !important;
        transition: all 0.3s ease !important;
    }
    
    div[data-baseweb="select"] > div:hover, div[data-baseweb="input"] > div:hover {
        border-color: #4CAF50 !important;
        box-shadow: 0 0 8px rgba(76, 175, 80, 0.2) !important;
    }

    /* 🌟 OCULTAR BOTONES + Y - DE LOS CAMPOS DE NÚMERO 🌟 */
    [data-testid="stNumberInputStepUp"], 
    [data-testid="stNumberInputStepDown"] {
        display: none !important;
    }

    /* 🌟 MEJORAR LAS TARJETAS DE MÉTRICAS 🌟 */
    div[data-testid="metric-container"] {
        background: linear-gradient(145deg, #1e1e1e, #121212);
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 12px;
        padding: 15px 20px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.4);
        transition: transform 0.3s ease, border-color 0.3s ease;
    }
    
    div[data-testid="metric-container"]:hover {
        transform: translateY(-3px);
        border-color: #4CAF50;
    }

    /* 🌟 ESTILIZAR LAS TABLAS (DataFrames) 🌟 */
    div[data-testid="stDataFrame"] > div {
        border-radius: 12px !important;
        border: 1px solid rgba(76, 175, 80, 0.2) !important; 
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.25) !important;
        overflow: hidden !important; 
        transition: box-shadow 0.3s ease, border-color 0.3s ease !important;
    }
    div[data-testid="stDataFrame"] > div:hover {
        border-color: #4CAF50 !important;
        box-shadow: 0 8px 20px rgba(76, 175, 80, 0.35) !important; 
    }

    /* 📱 OPTIMIZACIÓN RESPONSIVA EXCLUSIVA PARA MÓVILES 📱 */
    @media (max-width: 768px) {
        /* Fuerza a que las tarjetas personalizadas se apilen hacia abajo en vez de aplastarse */
        div[style*="flex: 1 1 calc"] {
            flex: 1 1 100% !important;
            min-width: 100% !important;
            margin-bottom: 10px !important;
        }
        /* Ajusta los tamaños de los textos gigantes para que no rompan la pantalla */
        h1 { font-size: 28px !important; }
        div[data-testid="metric-container"] h2 { font-size: 22px !important; }
    }
</style>
""", unsafe_allow_html=True)

# 2. Obligar a iOS a leer el logo usando JavaScript (Hack para iPhone)
try:
    with open("logo.png", "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
        
    icono_js = f"""
    <script>
        var doc = window.parent.document;
        var link = doc.querySelector("link[rel~='apple-touch-icon']");
        if (!link) {{
            link = doc.createElement('link');
            link.rel = 'apple-touch-icon';
            doc.head.appendChild(link);
        }}
        link.href = 'data:image/png;base64,{encoded_string}';
    </script>
    """
    components.html(icono_js, height=0, width=0)
except FileNotFoundError:
    pass

URL_GOOGLE_SHEET = "https://docs.google.com/spreadsheets/d/1lswvfo2ggmqvyslLCYj-WWpO56v0jgV0dVpNwXnEuDY/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

CATEGORIAS_BASE = ["Gasolina", "Pa La Semana", "Bebe", "Electricidad", "Gas", "Agua", "Gym", "Deuda", "Subs", "Pelo", "Otros", "Inversion", "Ahorro", "Disfrute", "Seguro"]
MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
MAPA_EMOJIS = {
    "Trading View": "📈",
    "Cuenta de fondeo": "🏦",
    "Fx Replay": "⏪",
    "Mentoria": "👨‍🏫"
}

# --- CARGAR DATOS (MEMORIA LOCAL) ---
def cargar_base_datos(nombre):
    # Ponemos ttl=0 para que al refrescar la página (Ctrl+R) obligue a buscar en Google Sheets
    try:
        df = conn.read(spreadsheet=URL_GOOGLE_SHEET, worksheet=nombre, ttl=0).dropna(how="all")
        if df.empty:
            columnas = {
                "Gastos_Fijos": ["Categoría", "Monto_Mensual", "Fondo_Disponible"],
                "Movimientos": ["Fecha", "Cuenta", "Concepto", "Monto"],
                "Cuentas": ["Cuenta", "Saldo"],
                "Excepciones": ["Cuenta", "Categoria_Excluida"],
                "Trading": ["Fecha", "Cuenta", "Tipo", "Concepto", "Monto"],
                "Cargos_Auto": ["Concepto", "Categoria", "Cuenta", "Monto", "Dia_Cobro", "Ultimo_Mes_Cobrado"]
            }
            return pd.DataFrame(columns=columnas.get(nombre, []))
        if nombre == "Gastos_Fijos" and "Fondo_Disponible" not in df.columns:
            df["Fondo_Disponible"] = 0.0
        return df
    except:
        return pd.DataFrame()

# Solo descargamos de Google Sheets si la app se acaba de abrir o se refrescó con F5
if 'df_fijos' not in st.session_state:
    st.session_state.df_fijos = cargar_base_datos("Gastos_Fijos")
    st.session_state.df_movs = cargar_base_datos("Movimientos")
    st.session_state.df_cuentas = cargar_base_datos("Cuentas")
    st.session_state.df_excep = cargar_base_datos("Excepciones")
    st.session_state.df_trading = cargar_base_datos("Trading")

# 🛡️ ESCUDO: Asegurarnos de que esta nueva tabla se cargue de forma independiente
if 'df_cargos_auto' not in st.session_state:
    st.session_state.df_cargos_auto = cargar_base_datos("Cargos_Auto")

# Usamos las variables de la sesión para que todo sea instantáneo
df_fijos = st.session_state.df_fijos
df_movs = st.session_state.df_movs
df_cuentas = st.session_state.df_cuentas
df_excep = st.session_state.df_excep
df_trading = st.session_state.df_trading # Nueva hoja cargada
df_cargos_auto = st.session_state.df_cargos_auto


# -----------------------------------------------------


# --- NAVEGACIÓN CON PESTAÑAS ESTILO BOTONES PREMIUM (INSTANTÁNEO) ---
# Usamos un contenedor HTML para forzar el nombre a la izquierda y permitir que las pestañas suban
st.markdown("<h1 style='position: absolute; top: 35px; left: 10px; color: #4CAF50; font-size: 45px; z-index: 100; font-weight: 800; display: flex; align-items: center;'>FINANCIAL CENTER</h1>", unsafe_allow_html=True)

st.markdown("""
<style>
    /* 1. Contenedor general de las pestañas */
    div[data-testid="stTabs"] {
        padding: 0px !important; 
        margin-top: 5px !important; /* Bajamos los botones 10px adicionales */
    }

    /* 2. Estilizar cada pestaña individualmente para simular un botón */
    div[data-testid="stTabs"] button {
        font-size: 16px !important; 
        font-weight: 700 !important;
        background-color: rgba(40, 40, 40, 0.6) !important; 
        border-radius: 10px !important; 
        padding: 10px 18px !important;
        margin: 0px 5px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.4) !important;
        transition: all 0.3s ease !important;
        color: #d1d1d1 !important;
    }

    /* 4. Efecto Hover */
    div[data-testid="stTabs"] button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0px 8px 15px rgba(76, 175, 80, 0.3) !important;
        border-color: #4CAF50 !important;
        color: #ffffff !important;
    }

    /* 5. Estilo de la pestaña seleccionada (ACTIVA) */
    div[data-testid="stTabs"] button[aria-selected="true"] {
        background: linear-gradient(145deg, #4CAF50, #2E7D32) !important;
        color: white !important;
        box-shadow: 0px 0px 15px rgba(76, 175, 80, 0.5) !important; 
        border: none !important;
        transform: scale(1.02) !important;
    }

    /* 6. ALINEAR OPCIONES A LA DERECHA */
    div[data-testid="stTabs"] [data-baseweb="tab-highlight-point"] {
        display: none !important;
    }
    div[data-baseweb="tab-list"] {
        gap: 10px !important;
        border-bottom: none !important;
        justify-content: flex-end !important; /* ESTO MUEVE LOS BOTONES A LA DERECHA */
        padding-top: 15px !important;
        padding-bottom: 10px !important;
    }

    /* 🚫 ELIMINAR FLECHAS DE DESPLAZAMIENTO DE LAS PESTAÑAS 🚫 */
    div[data-baseweb="tab-list"] button:not([role="tab"]) {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

tab_ajustes, tab_pagos, tab_trading, tab_vista, tab_cuentas = st.tabs([
    "⚙️ GASTOS FIJOS", 
    "💸 REGISTRAR GASTOS", 
    "📈 TRADING", 
    "📊 PROYECCIÓN ANUAL", 
    "💳 MIS CUENTAS"
])

# ---------------------------------------------------------
# 1. VISTA: PROYECCIÓN ANUAL 
# ---------------------------------------------------------
with tab_vista:
    if not df_fijos.empty:
        df_fijos["Monto_Mensual"] = pd.to_numeric(df_fijos["Monto_Mensual"]).fillna(0)
        total_m = df_fijos["Monto_Mensual"].sum()
        
        # Métricas Premium Neón para Proyección Anual
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f'<div style="background: linear-gradient(145deg, #1e1e1e, #121212); border-bottom: 3px solid #00E5FF; padding: 15px 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.3);"><p style="color: #888; font-size: 12px; font-weight: bold; margin:0; text-transform: uppercase; letter-spacing: 1px;">Presupuesto Mensual</p><h2 style="color: #00E5FF; margin:0; font-size: 28px;">${total_m:,.0f}</h2></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div style="background: linear-gradient(145deg, #1e1e1e, #121212); border-bottom: 3px solid #B388FF; padding: 15px 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.3);"><p style="color: #888; font-size: 12px; font-weight: bold; margin:0; text-transform: uppercase; letter-spacing: 1px;">Inyección Semanal</p><h2 style="color: #B388FF; margin:0; font-size: 28px;">${total_m/4:,.0f}</h2></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div style="background: linear-gradient(145deg, #1e1e1e, #121212); border-bottom: 3px solid #69F0AE; padding: 15px 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.3);"><p style="color: #888; font-size: 12px; font-weight: bold; margin:0; text-transform: uppercase; letter-spacing: 1px;">Proyección Anual</p><h2 style="color: #69F0AE; margin:0; font-size: 28px;">${total_m*12:,.0f}</h2></div>', unsafe_allow_html=True)
        
        st.write("")
        st.write("")
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            fig1 = px.pie(df_fijos, values='Monto_Mensual', names='Categoría', hole=0.5, title="Reparto por Categoría")
            fig1.update_layout(title_x=0.5, margin=dict(t=60)) 
            # 🌟 ESTO ELIMINA LA BARRA DE ZOOM Y BOTONES POR COMPLETO 🌟
            st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})
        with col_g2:
            fig2 = px.bar(df_fijos, x='Categoría', y='Monto_Mensual', title="Presupuesto por Categoría", color='Categoría')
            fig2.update_layout(title_x=0.5, margin=dict(t=60))
            # 🌟 ESTO ELIMINA LA BARRA DE ZOOM Y BOTONES POR COMPLETO 🌟
            st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})

        st.markdown("#### 🗓️ Tabla de Proyección a 12 Meses")
        df_anual = pd.DataFrame(index=MESES, columns=df_fijos["Categoría"].tolist())
        for cat in df_fijos["Categoría"]:
            monto = df_fijos.loc[df_fijos["Categoría"] == cat, "Monto_Mensual"].values[0]
            df_anual[cat] = monto
        df_anual["TOTAL MES"] = df_anual.sum(axis=1)
        df_anual.loc["TOTAL ANUAL"] = df_anual.sum()
        
        # 🌟 DISEÑO DE TARJETAS PARA PROYECCIÓN A 12 MESES (CERO TABLAS) 🌟
        html_anual = '<div style="display: flex; flex-wrap: wrap; gap: 15px; margin-top: 10px;">'
        
        # Iteramos sobre los meses (excluyendo la fila de 'TOTAL ANUAL')
        meses_solo = [m for m in df_anual.index if m != "TOTAL ANUAL"]
        
        for mes in meses_solo:
            # Extraemos el total de ese mes de manera segura
            try:
                total_mes = float(str(df_anual.loc[mes, "TOTAL MES"]).replace("$", "").replace(",", ""))
            except ValueError:
                total_mes = 0.0
                
            # Tarjeta de cada mes (Todo en una línea para Streamlit)
            html_anual += f'<div style="background: linear-gradient(145deg, #2a2a2a, #1a1a1a); border-top: 4px solid #2E7D32; padding: 15px; border-radius: 10px; flex: 1 1 calc(25% - 15px); min-width: 130px; box-shadow: 0 4px 8px rgba(0,0,0,0.3); text-align: center;"><h4 style="margin: 0 0 8px 0; color: #aaa; font-size: 14px; letter-spacing: 1px; text-transform: uppercase;">{mes}</h4><span style="color: #69F0AE; font-weight: bold; font-size: 20px;">${total_mes:,.0f}</span></div>'
            
        # Tarjeta ancha especial para el TOTAL ANUAL al final
        try:
            total_anual_val = float(str(df_anual.loc["TOTAL ANUAL", "TOTAL MES"]).replace("$", "").replace(",", ""))
        except ValueError:
            total_anual_val = 0.0
            
        html_anual += f'<div style="background: linear-gradient(145deg, #1e1e1e, #121212); border-left: 5px solid #00E5FF; padding: 20px; border-radius: 10px; flex: 1 1 100%; box-shadow: 0 4px 12px rgba(0,0,0,0.4); display: flex; justify-content: space-between; align-items: center; margin-top: 5px;"><span style="color: #fff; font-size: 18px; font-weight: bold; letter-spacing: 1px;">TOTAL ACUMULADO DEL AÑO</span><span style="color: #00E5FF; font-weight: bold; font-size: 28px;">${total_anual_val:,.0f}</span></div>'
        
        html_anual += '</div>'
        st.markdown(html_anual, unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. AJUSTES: GASTOS FIJOS 
# ---------------------------------------------------------
with tab_ajustes:
    # 🌟 Recuperamos el Título 🌟
    st.markdown("<h3 style='margin-top: 10px; color: #fff;'>Panel de Gastos Fijos</h3>", unsafe_allow_html=True)

    if not df_fijos.empty:
        df_order = df_fijos.copy()
        df_order["Monto Semanal"] = pd.to_numeric(df_order["Monto_Mensual"]) / 4
        df_order["Monto Anual"] = pd.to_numeric(df_order["Monto_Mensual"]) * 12
        df_order["Fondo_Disponible"] = pd.to_numeric(df_order["Fondo_Disponible"])
        
        # 🌟 MAGIA: ORDENAR LOS 0 AL FINAL 🌟
        # Creamos una condición temporal para saber si el fondo está en 0
        df_order["Es_Cero"] = df_order["Fondo_Disponible"] == 0
        # Ordenamos primero asegurando que los Es_Cero=False vayan arriba, 
        # y luego los ordenamos por la cantidad de dinero (de mayor a menor)
        df_order = df_order.sort_values(by=["Es_Cero", "Fondo_Disponible"], ascending=[True, False])
        
        # Orden pedido de columnas original (y limpiamos la columna temporal)
        df_order = df_order[["Categoría", "Monto Semanal", "Monto_Mensual", "Monto Anual", "Fondo_Disponible"]]
        
        # 🌟 TARJETAS DE TOTALES (NUEVO) 🌟
        total_fondo = df_order["Fondo_Disponible"].sum()
        total_mensual = df_order["Monto_Mensual"].sum()
        
        st.markdown(f'''
        <div style="display: flex; gap: 15px; margin-bottom: 20px;">
            <div style="background: linear-gradient(145deg, #1e1e1e, #121212); padding: 12px 20px; border-radius: 8px; border-left: 4px solid #4CAF50; box-shadow: 0 4px 6px rgba(0,0,0,0.3); flex: 1;">
                <span style="color: #888; font-size: 11px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px;">Suma Total de Fondos</span><br>
                <span style="color: #4CAF50; font-size: 24px; font-weight: bold;">${total_fondo:,.2f}</span>
            </div>
            <div style="background: linear-gradient(145deg, #1e1e1e, #121212); padding: 12px 20px; border-radius: 8px; border-left: 4px solid #1565C0; box-shadow: 0 4px 6px rgba(0,0,0,0.3); flex: 1;">
                <span style="color: #888; font-size: 11px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px;">Suma de Gasto Mensual</span><br>
                <span style="color: #1565C0; font-size: 24px; font-weight: bold;">${total_mensual:,.2f}</span>
            </div>
        </div>
        ''', unsafe_allow_html=True)

        # 🌟 DISEÑO DE TARJETAS INDIVIDUALES (CERO TABLAS) 🌟
        html_gastos = '<div style="display: flex; flex-wrap: wrap; gap: 15px; margin-top: 5px;">'
        
        for _, row in df_order.iterrows():
            # Limpieza segura de números
            try: fondo = float(str(row["Fondo_Disponible"]).replace("$", "").replace(",", ""))
            except ValueError: fondo = 0.0
            try: semanal = float(str(row["Monto Semanal"]).replace("$", "").replace(",", ""))
            except ValueError: semanal = 0.0
            try: mensual = float(str(row["Monto_Mensual"]).replace("$", "").replace(",", ""))
            except ValueError: mensual = 0.0
            try: anual = float(str(row["Monto Anual"]).replace("$", "").replace(",", ""))
            except ValueError: anual = 0.0
                
            color_fondo_txt = "#4CAF50" if fondo > 0 else ("#F44336" if fondo < 0 else "#888888")
            
            # Tarjeta tipo Widget (Todo en una línea para que Streamlit no lo rompa)
            html_gastos += f'<div style="background: linear-gradient(145deg, #2a2a2a, #1a1a1a); border-top: 4px solid #1565C0; padding: 15px; border-radius: 10px; flex: 1 1 calc(25% - 15px); min-width: 200px; box-shadow: 0 4px 8px rgba(0,0,0,0.3);"><h4 style="margin: 0 0 12px 0; color: #fff; text-align: center; font-size: 18px; letter-spacing: 1px;">{row["Categoría"]}</h4><div style="display: flex; justify-content: space-between; margin-bottom: 6px;"><span style="color: #888; font-size: 13px;">Semanal:</span><span style="color: #ddd; font-weight: bold; font-size: 14px;">${semanal:,.0f}</span></div><div style="display: flex; justify-content: space-between; margin-bottom: 6px;"><span style="color: #888; font-size: 13px;">Mensual:</span><span style="color: #ddd; font-weight: bold; font-size: 14px;">${mensual:,.0f}</span></div><div style="display: flex; justify-content: space-between; margin-bottom: 6px;"><span style="color: #888; font-size: 13px;">Anual:</span><span style="color: #ddd; font-weight: bold; font-size: 14px;">${anual:,.0f}</span></div><hr style="border: 0; border-top: 1px solid rgba(255,255,255,0.1); margin: 10px 0;"><div style="display: flex; justify-content: space-between; align-items: center;"><span style="color: #aaa; font-size: 13px; font-weight: bold;">Fondo Actual:</span><span style="color: {color_fondo_txt}; font-weight: bold; font-size: 18px;">${fondo:,.0f}</span></div></div>'
            
        html_gastos += '</div>'
        st.markdown(html_gastos, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True) # Espacio antes del desplegable

    # DESPLEGABLE MOVIDO AL FINAL
    with st.expander("Configurar Gastos Fijos", expanded=False):
        cat_existentes = df_fijos["Categoría"].tolist() if not df_fijos.empty else []
        todas_categorias = sorted(list(set(CATEGORIAS_BASE + cat_existentes)))
        
        c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
        with c1: cat_sel = st.selectbox("Selecciona Categoría", todas_categorias)
        
        m_act, f_act = 0.0, 0.0
        if not df_fijos.empty and cat_sel in df_fijos["Categoría"].values:
            m_act = float(df_fijos.loc[df_fijos["Categoría"] == cat_sel, "Monto_Mensual"].values[0])
            f_act = float(df_fijos.loc[df_fijos["Categoría"] == cat_sel, "Fondo_Disponible"].values[0])
            
        with c2: m_sel = st.number_input("Monto Mensual ($)", value=m_act)
        with c3: f_sel = st.number_input("Ajustar Fondo ($)", value=f_act)
        with c4:
            st.write("")
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("💾", help="Guardar/Actualizar", use_container_width=True, type="primary"):
                    if not df_fijos.empty and cat_sel in df_fijos["Categoría"].values:
                        df_fijos.loc[df_fijos["Categoría"] == cat_sel, "Monto_Mensual"] = m_sel
                        df_fijos.loc[df_fijos["Categoría"] == cat_sel, "Fondo_Disponible"] = f_sel
                    else:
                        nuevo = pd.DataFrame([{"Categoría": cat_sel, "Monto_Mensual": m_sel, "Fondo_Disponible": f_sel}])
                        df_fijos = pd.concat([df_fijos, nuevo], ignore_index=True)
                    conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
                    st.session_state.df_fijos = df_fijos 
                    st.rerun()
            with col_btn2:
                if st.button("🗑️", help="Eliminar Categoría", use_container_width=True):
                    if not df_fijos.empty and cat_sel in df_fijos["Categoría"].values:
                        df_fijos = df_fijos[df_fijos["Categoría"] != cat_sel]
                        conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
                        st.cache_data.clear()
                        st.rerun()

# ---------------------------------------------------------
# 3. PAGOS Y EXCEPCIONES (Filtro Maestro por Cuenta)
# ---------------------------------------------------------
# ---------------------------------------------------------
# 3. PAGOS Y EXCEPCIONES (Filtro Maestro por Cuenta)
# ---------------------------------------------------------
with tab_pagos:
    # 🌟 TODO EL PANEL UNIFICADO EN UN FRAGMENTO PARA EVITAR PARPADEOS 🌟
    @st.fragment
    def mostrar_panel_pagos_unificado():
        # Conectamos con la memoria global de la app
        global df_fijos, df_movs, df_cuentas, df_excep, df_trading, df_cargos_auto
    
        
        nombres_cuentas = df_cuentas["Cuenta"].tolist() if not df_cuentas.empty else []
        
        # 🟢 FIX DEFINITIVO: Columnas principales aplanadas para que Streamlit no oculte los botones
        col_cuenta, col_btn_add, col_btn_undo = st.columns([1.8, 1, 1])
        
        with col_cuenta:
            opciones_inyec = ["TODAS"] + nombres_cuentas
            # Este es el FILTRO MAESTRO: Todo lo que veas abajo será de esta cuenta
            cuenta_maestra = st.selectbox("Cuenta", opciones_inyec, key="cuenta_maestra_select")
       
            if cuenta_maestra != "TODAS":
                # Mostramos las excepciones solo de la cuenta seleccionada
                exc_c = df_excep[df_excep["Cuenta"] == cuenta_maestra]["Categoria_Excluida"].tolist() if not df_excep.empty else []
                categorias_v = df_fijos["Categoría"].tolist() if not df_fijos.empty else []
                exc_c_v = [cat for cat in exc_c if cat in categorias_v]
                
                with st.form("form_excepciones_nuevo", border=False):
                    nuevas_exc = st.multiselect(f"Excluir categorías en {cuenta_maestra}:", categorias_v, default=exc_c_v, key="multiselect_exc")
                    btn_guardar_exc = st.form_submit_button("💾 Guardar en Excel")
                    
                if btn_guardar_exc:
                    df_temp = conn.read(spreadsheet=URL_GOOGLE_SHEET, worksheet="Excepciones", ttl=0).dropna(how="all")
                    if not df_temp.empty:
                        df_temp = df_temp[df_temp["Cuenta"] != cuenta_maestra]
                    nuevas_rows = pd.DataFrame([{"Cuenta": cuenta_maestra, "Categoria_Excluida": x} for x in nuevas_exc])
                    df_final_excep = pd.concat([df_temp, nuevas_rows], ignore_index=True)
                    conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Excepciones", data=df_final_excep)
                    st.session_state.df_excep = df_final_excep
                    st.success(f"Configuración de {cuenta_maestra} guardada.")
                    st.rerun()
                    
        st.markdown("<h4 style='color: #2E7D32;'>Aplicar Gasto</h4>", unsafe_allow_html=True)
        with col_btn_add:
            st.write("") # Empuja el botón hacia abajo para alinearlo
            st.write("")
            if st.button("AGREGAR SEMANA", use_container_width=True, type="primary", key="btn_agregar_semana_principal"):
                ctas_a_procesar = nombres_cuentas if cuenta_maestra == "TODAS" else [cuenta_maestra]
                for cta in ctas_a_procesar:
                    l_negra = df_excep[df_excep["Cuenta"] == cta]["Categoria_Excluida"].tolist() if not df_excep.empty else []
                    cats_v = df_fijos[~df_fijos["Categoría"].isin(l_negra)].copy()
                    monto_inyec = (pd.to_numeric(cats_v["Monto_Mensual"]) / 4).sum()
                    
                    for idx, row in cats_v.iterrows():
                        idx_f = df_fijos.index[df_fijos["Categoría"] == row["Categoría"]].tolist()[0]
                        df_fijos.at[idx_f, "Fondo_Disponible"] = float(df_fijos.at[idx_f, "Fondo_Disponible"]) + (float(row["Monto_Mensual"]) / 4)
                    
                    idx_c = df_cuentas.index[df_cuentas["Cuenta"] == cta].tolist()[0]
                    df_cuentas.at[idx_c, "Saldo"] = float(df_cuentas.at[idx_c, "Saldo"]) + monto_inyec
                    
                    nuevo_m = pd.DataFrame([{"Fecha": datetime.now().strftime("%Y-%m-%d"), "Cuenta": cta, "Concepto": "NÓMINA SEMANAL", "Monto": monto_inyec}])
                    df_movs = pd.concat([df_movs, nuevo_m], ignore_index=True)

                for cta_inv in (nombres_cuentas if cuenta_maestra == "TODAS" else [cuenta_maestra]):
                    l_negra_inv = df_excep[df_excep["Cuenta"] == cta_inv]["Categoria_Excluida"].tolist() if not df_excep.empty else []
                    if "Inversion" not in l_negra_inv and "Inversion" in df_fijos["Categoría"].values:
                        monto_inv_sem = float(df_fijos.loc[df_fijos["Categoría"] == "Inversion", "Monto_Mensual"].values[0]) / 4
                        nueva_op_t = pd.DataFrame([{
                            "Fecha": datetime.now().strftime("%Y-%m-%d"), 
                            "Cuenta": cta_inv, 
                            "Tipo": "Inyección Semanal", 
                            "Concepto": "Fondo Semanal", 
                            "Monto": -monto_inv_sem 
                        }])
                        df_trading = pd.concat([df_trading, nueva_op_t], ignore_index=True)

                conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
                conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Cuentas", data=df_cuentas)
                conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Movimientos", data=df_movs)
                conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Trading", data=df_trading)
                st.session_state.df_fijos, st.session_state.df_cuentas, st.session_state.df_movs, st.session_state.df_trading = df_fijos, df_cuentas, df_movs, df_trading
                st.rerun()
        
        with col_btn_undo:
            st.write("") # Empuja el botón hacia abajo para alinearlo
            st.write("")
            if st.button("DESHACER", use_container_width=True, key="btn_deshacer_semana_principal"):
                if not df_movs.empty and "NÓMINA SEMANAL" in df_movs["Concepto"].values:
                    ult_f = df_movs[df_movs["Concepto"] == "NÓMINA SEMANAL"]["Fecha"].iloc[-1]
                    a_revertir = df_movs[(df_movs["Concepto"] == "NÓMINA SEMANAL") & (df_movs["Fecha"] == ult_f)]
                    
                    for _, mov in a_revertir.iterrows():
                        c_r, m_r = mov["Cuenta"], float(mov["Monto"])
                        if c_r in df_cuentas["Cuenta"].values:
                            idx_c = df_cuentas.index[df_cuentas["Cuenta"] == c_r].tolist()[0]
                            df_cuentas.at[idx_c, "Saldo"] = float(df_cuentas.at[idx_c, "Saldo"]) - m_r
                        
                        l_n = df_excep[df_excep["Cuenta"] == c_r]["Categoria_Excluida"].tolist() if not df_excep.empty else []
                        for _, r in df_fijos[~df_fijos["Categoría"].isin(l_n)].iterrows():
                            idx_f = df_fijos.index[df_fijos["Categoría"] == r["Categoría"]].tolist()[0]
                            df_fijos.at[idx_f, "Fondo_Disponible"] = float(df_fijos.at[idx_f, "Fondo_Disponible"]) - (float(r["Monto_Mensual"]) / 4)
                    
                    df_movs = df_movs.drop(a_revertir.index)
                    
                    if not df_trading.empty:
                        fecha_str = str(ult_f).strip()
                        mask_t = (df_trading["Tipo"] == "Inyección Semanal") & (df_trading["Fecha"].astype(str).str.strip() == fecha_str)
                        df_trading = df_trading[~mask_t]
  
                    conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
                    conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Cuentas", data=df_cuentas)
                    conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Movimientos", data=df_movs)
                    conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Trading", data=df_trading)
                    
                    st.session_state.df_fijos = df_fijos
                    st.session_state.df_cuentas = df_cuentas
                    st.session_state.df_movs = df_movs
                    st.session_state.df_trading = df_trading
                    
                    st.success("✅ Semana deshecha correctamente.")
                    st.rerun()
                else:
                    st.warning("No hay inyección reciente para deshacer.")
                    st.rerun()

  
        # --- FORMULARIO DE GASTO ---
        st.markdown("<h4 style='color: #2E7D32;'>Aplicar Gasto</h4>", unsafe_allow_html=True)
        with st.form("form_gasto_unificado_nuevo", border=False):
            cg1, cg2, cg3, cg4 = st.columns([1.5, 1.5, 1, 1.2])
            with cg1: c_gasto = st.selectbox("Cuenta:", nombres_cuentas, index=nombres_cuentas.index(cuenta_maestra) if cuenta_maestra in nombres_cuentas else 0, key="gasto_cuenta_sel")
            with cg2: 
                # 🌟 LISTA COMPLETA: Muestra absolutamente todas las categorías de la base de datos (Inversión, Inyección del trading, etc.)
                lista_sobres_completos = df_fijos["Categoría"].tolist() if not df_fijos.empty else []
                s_gasto = st.selectbox("Categoría:", lista_sobres_completos, key="gasto_cat_sel")
            with cg3: m_gasto = st.number_input("Monto:", min_value=0.0, key="gasto_monto_input")
            with cg4: 
                st.write("")
                if st.form_submit_button("APLICAR GASTO", use_container_width=True, type="primary"):
                    if m_gasto > 0:
                        nuevo_m = pd.DataFrame([{"Fecha": datetime.now().strftime("%Y-%m-%d"), "Cuenta": c_gasto, "Concepto": s_gasto, "Monto": -m_gasto}])
                        df_movs = pd.concat([df_movs, nuevo_m], ignore_index=True)
             
                        idx_f = df_fijos.index[df_fijos["Categoría"] == s_gasto].tolist()[0]
                        df_fijos.at[idx_f, "Fondo_Disponible"] = float(df_fijos.at[idx_f, "Fondo_Disponible"]) - m_gasto
                        # 🌟 MAGIA: Si el gasto es Inversión, enviarlo a Trading automáticamente 🌟
                        if s_gasto == "Inversion":
                            nueva_op_t = pd.DataFrame([{"Fecha": datetime.now().strftime("%Y-%m-%d"), "Cuenta": c_gasto, "Tipo": "Inversión", "Concepto": "Gasto Manual Inversión", "Monto": m_gasto}])
                            df_trading = pd.concat([df_trading, nueva_op_t], ignore_index=True)
                            conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Trading", data=df_trading)
                            st.session_state.df_trading = df_trading

                        conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Movimientos", data=df_movs)
                        conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
   
                        st.session_state.df_movs, st.session_state.df_fijos = df_movs, df_fijos
                        st.rerun()

        # 🔄 APARTADO NUEVO: MOVER DINERO ENTRE SOBRES (PRESTAR ENTRE CATEGORÍAS) 🔄
        with st.expander("Mover Dinero"):
            with st.form("form_mover_entre_sobres_interno", border=False):
                cm1, cm2, cm3 = st.columns([2, 2, 1])
                with cm1: cat_origen = st.selectbox("De:", df_fijos["Categoría"].tolist() if not df_fijos.empty else [], key="mov_sobres_origen")
                with cm2: cat_destino = st.selectbox("A:", df_fijos["Categoría"].tolist() if not df_fijos.empty else [], key="mov_sobres_destino")
                with cm3: monto_a_mover = st.number_input("Monto ($):", min_value=0.0, step=10.0, key="mov_sobres_monto")
                
                if st.form_submit_button("REALIZAR TRASPASO", use_container_width=True, type="primary"):
                    if monto_a_mover > 0 and cat_origen != cat_destino:
                        idx_o = df_fijos.index[df_fijos["Categoría"] == cat_origen].tolist()[0]
                        idx_d = df_fijos.index[df_fijos["Categoría"] == cat_destino].tolist()[0]
                        
                        # Matemáticas de traspaso interno
                        df_fijos.at[idx_o, "Fondo_Disponible"] = float(df_fijos.at[idx_o, "Fondo_Disponible"]) - monto_a_mover
                        df_fijos.at[idx_d, "Fondo_Disponible"] = float(df_fijos.at[idx_d, "Fondo_Disponible"]) + monto_a_mover
                        
                        # Dejamos un rastro en el historial para saber qué se prestó
                        nuevo_mov_traspaso = pd.DataFrame([{"Fecha": datetime.now().strftime("%Y-%m-%d"), "Cuenta": "SISTEMA", "Concepto": f"TRASPASO: {cat_origen} ➔ {cat_destino}", "Monto": 0.0}])
                        df_movs = pd.concat([df_movs, nuevo_mov_traspaso], ignore_index=True)
                        
                        # Guardamos en Google Sheets
                        conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
                        conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Movimientos", data=df_movs)
                        
                        st.session_state.df_fijos = df_fijos
                        st.session_state.df_movs = df_movs
                        st.success(f"✅ Se movieron ${monto_a_mover:,.2f} de '{cat_origen}' a '{cat_destino}' correctamente.")
                        st.rerun()

# --- 1. SECCIÓN DISPONIBLE (TODO ARRIBA) ---
        st.markdown(f"<h4 style='color: #2E7D32;'>Disponible en: {cuenta_maestra}</h4>", unsafe_allow_html=True)
        l_n_v = df_excep[df_excep["Cuenta"] == cuenta_maestra]["Categoria_Excluida"].tolist() if (not df_excep.empty and cuenta_maestra != "TODAS") else []
        df_sobres = df_fijos[~df_fijos["Categoría"].isin(l_n_v)]
        
        # Tarjetas en cuadrícula (Ocupan el 100% del ancho dividiéndose en bloques)
        html_s = '<div style="display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 20px;">'
        for _, r in df_sobres.iterrows():
            f = float(str(r["Fondo_Disponible"]).replace("$", "").replace(",", ""))
            c = "#4CAF50" if f >= 0 else "#F44336"
            html_s += f'<div style="background: #1a1a1a; border-left: 4px solid {c}; padding: 15px; border-radius: 8px; flex: 1 1 calc(25% - 10px); min-width: 150px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 6px rgba(0,0,0,0.3);"><span style="font-size: 15px; font-weight: bold; color: #ccc;">{r["Categoría"]}</span><span style="color: {c}; font-weight: bold; font-size: 18px;">${f:,.0f}</span></div>'
        st.markdown(html_s + '</div>', unsafe_allow_html=True)

        st.markdown("<hr style='border-color: rgba(255,255,255,0.1); margin: 10px 0 20px 0;'>", unsafe_allow_html=True)

        # --- 2. SECCIÓN HISTORIAL (TODO ABAJO) ---
        st.markdown(f"<h4 style='color: #1565C0;'>Historial de Movimientos</h4>", unsafe_allow_html=True)
        df_h = df_movs.copy()
        if cuenta_maestra != "TODAS": df_h = df_h[df_h["Cuenta"] == cuenta_maestra]
        
        # Extraer fechas para el filtro
        opciones_tiempo = ["TODO"]
        meses_es = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
        if not df_h.empty:
            df_h["Fecha_DT"] = pd.to_datetime(df_h["Fecha"], errors='coerce')
            año_actual = datetime.now().year
            meses_con_datos = df_h[df_h["Fecha_DT"].dt.year == año_actual]["Fecha_DT"].dt.month.dropna().unique()
            opciones_tiempo += [meses_es[m] for m in sorted(meses_con_datos)]
            años_con_datos = df_h["Fecha_DT"].dt.year.dropna().unique()
            opciones_tiempo += [str(int(a)) for a in sorted(años_con_datos, reverse=True) if a < año_actual]

        col_fh1, col_fh2 = st.columns(2)
        with col_fh1:
            f_cat = st.selectbox("Filtrar Categoría:", ["VER TODO"] + df_fijos["Categoría"].tolist(), key="filtrar_cat_historial_sel")
        with col_fh2:
            f_fecha = st.selectbox("Filtrar Tiempo:", opciones_tiempo, key="filtrar_fecha_historial")
        
        if f_cat != "VER TODO": df_h = df_h[df_h["Concepto"] == f_cat]
        
        if not df_h.empty and f_fecha != "TODO":
            if f_fecha in meses_es.values():
                mes_num = list(meses_es.keys())[list(meses_es.values()).index(f_fecha)]
                df_h = df_h[(df_h["Fecha_DT"].dt.month == mes_num) & (df_h["Fecha_DT"].dt.year == año_actual)]
            else:
                df_h = df_h[df_h["Fecha_DT"].dt.year == int(f_fecha)]
                
        if not df_h.empty and "Fecha_DT" in df_h.columns:
            df_h = df_h.drop(columns=["Fecha_DT"])

        df_h = df_h.sort_index(ascending=False)

        # 🌟 FEED DE TARJETAS (MISMO DISEÑO Y ESPACIO QUE TRADING) 🌟
        st.markdown('<div style="max-height: 450px; overflow-y: auto; padding-right: 10px; margin-top: 10px;">', unsafe_allow_html=True)
        
        for idx_h, r_h in df_h.iterrows():
            m_h = float(r_h["Monto"])
            c_h = "#4CAF50" if m_h >= 0 else "#F44336"
            icon_h = "💰" if m_h >= 0 else "💸"
            
            col_h1, col_h_edit, col_h_del = st.columns([6, 0.35, 0.35], gap="small")
            
            with col_h1:
                tj = f'<div style="background: linear-gradient(145deg, #1e1e1e, #121212); margin-bottom: 8px; padding: 15px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.03); display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 6px rgba(0,0,0,0.2);"><div style="display: flex; align-items: center; gap: 15px;"><div style="font-size: 24px;">{icon_h}</div><div><div style="font-size: 15px; font-weight: bold; color: #fff;">{r_h["Concepto"]}</div><div style="font-size: 11px; color: #888; text-transform: uppercase;">{r_h["Fecha"]} • {r_h["Cuenta"]}</div></div></div><div style="color: {c_h}; font-weight: bold; font-size: 18px;">${abs(m_h):,.2f}</div></div>'
                st.markdown(tj, unsafe_allow_html=True)
            
            with col_h_edit:
                st.write("")
                if st.button("✏️", key=f"ed_h_{idx_h}", help="Editar Gasto"):
                    st.session_state[f"edit_h_{idx_h}"] = not st.session_state.get(f"edit_h_{idx_h}", False)
                    st.session_state[f"del_h_{idx_h}"] = False
            
            with col_h_del:
                st.write("")
                if st.button("🗑️", key=f"rm_h_{idx_h}", help="Borrar Gasto"):
                    st.session_state[f"del_h_{idx_h}"] = not st.session_state.get(f"del_h_{idx_h}", False)
                    st.session_state[f"edit_h_{idx_h}"] = False
            
            # --- LÓGICA BORRAR (RESTAURA SALDOS AUTOMÁTICAMENTE) ---
            if st.session_state.get(f"del_h_{idx_h}", False):
                st.warning("⚠️ ¿Borrar este movimiento y devolver el dinero a las cuentas?")
                cy_h, cn_h = st.columns(2)
                if cy_h.button("✅ Sí, Borrar", key=f"y_h_{idx_h}"):
                    cta_del, conc_del, monto_del = r_h["Cuenta"], r_h["Concepto"], float(r_h["Monto"])
                    
                    if cta_del in df_cuentas["Cuenta"].values:
                        i_c = df_cuentas.index[df_cuentas["Cuenta"] == cta_del].tolist()[0]
                        df_cuentas.at[i_c, "Saldo"] = float(df_cuentas.at[i_c, "Saldo"]) - monto_del
                        
                    if conc_del in df_fijos["Categoría"].values:
                        i_f = df_fijos.index[df_fijos["Categoría"] == conc_del].tolist()[0]
                        df_fijos.at[i_f, "Fondo_Disponible"] = float(df_fijos.at[i_f, "Fondo_Disponible"]) - monto_del
                        
                    df_movs = df_movs.drop(idx_h)
                    
                    conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Movimientos", data=df_movs)
                    conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Cuentas", data=df_cuentas)
                    conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
                    st.session_state.df_movs, st.session_state.df_cuentas, st.session_state.df_fijos = df_movs, df_cuentas, df_fijos
                    st.session_state[f"del_h_{idx_h}"] = False
                    st.rerun()
                if cn_h.button("❌ Cancelar", key=f"n_h_{idx_h}"):
                    st.session_state[f"del_h_{idx_h}"] = False
                    st.rerun()

            # --- LÓGICA EDITAR (AJUSTA MATEMÁTICAS AUTOMÁTICAMENTE) ---
            if st.session_state.get(f"edit_h_{idx_h}", False):
                st.markdown("<div style='background: #262730; padding: 15px; border-radius: 10px; margin-bottom: 20px;'>", unsafe_allow_html=True)
                ce_h1, ce_h2 = st.columns([2, 1])
                new_conc_h = ce_h1.selectbox("Cambiar Categoría:", df_fijos["Categoría"].tolist(), index=df_fijos["Categoría"].tolist().index(r_h["Concepto"]) if r_h["Concepto"] in df_fijos["Categoría"].values else 0, key=f"in_ch_{idx_h}")
                new_mon_h = ce_h2.number_input("Modificar Monto ($):", value=float(abs(r_h["Monto"])), min_value=0.0, key=f"in_mh_{idx_h}")
                
                if st.button("💾 GUARDAR CAMBIOS", key=f"sv_h_{idx_h}", use_container_width=True, type="primary"):
                    cta_ed, conc_old, monto_old = r_h["Cuenta"], r_h["Concepto"], float(r_h["Monto"])
                    
                    # 1. Revertir impacto del gasto viejo
                    if cta_ed in df_cuentas["Cuenta"].values:
                        i_c = df_cuentas.index[df_cuentas["Cuenta"] == cta_ed].tolist()[0]
                        df_cuentas.at[i_c, "Saldo"] = float(df_cuentas.at[i_c, "Saldo"]) - monto_old
                    if conc_old in df_fijos["Categoría"].values:
                        i_f = df_fijos.index[df_fijos["Categoría"] == conc_old].tolist()[0]
                        df_fijos.at[i_f, "Fondo_Disponible"] = float(df_fijos.at[i_f, "Fondo_Disponible"]) - monto_old
                        
                    # 2. Aplicar el impacto del gasto nuevo
                    monto_nuevo_real = -new_mon_h if monto_old < 0 else new_mon_h # Mantiene el signo negativo si era un gasto
                    if cta_ed in df_cuentas["Cuenta"].values:
                        i_c = df_cuentas.index[df_cuentas["Cuenta"] == cta_ed].tolist()[0]
                        df_cuentas.at[i_c, "Saldo"] = float(df_cuentas.at[i_c, "Saldo"]) + monto_nuevo_real
                    if new_conc_h in df_fijos["Categoría"].values:
                        i_f = df_fijos.index[df_fijos["Categoría"] == new_conc_h].tolist()[0]
                        df_fijos.at[i_f, "Fondo_Disponible"] = float(df_fijos.at[i_f, "Fondo_Disponible"]) + monto_nuevo_real
                        
                    # 3. Guardar en base de datos
                    df_movs.at[idx_h, "Concepto"] = new_conc_h
                    df_movs.at[idx_h, "Monto"] = monto_nuevo_real
                    
                    conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Movimientos", data=df_movs)
                    conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Cuentas", data=df_cuentas)
                    conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
                    st.session_state.df_movs, st.session_state.df_cuentas, st.session_state.df_fijos = df_movs, df_cuentas, df_fijos
                    st.session_state[f"edit_h_{idx_h}"] = False
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
                
        st.markdown('</div>', unsafe_allow_html=True)
        
        # BALANCE TOTAL DEL HISTORIAL FILTRADO
        t_h = df_h["Monto"].sum()
        c_t = "#4CAF50" if t_h >= 0 else "#F44336"
        st.markdown(f'<div style="background: linear-gradient(145deg, #121212, #0a0a0a); margin-top: 15px; padding: 15px; border-radius: 10px; border-top: 2px solid {c_t}; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 -4px 10px rgba(0,0,0,0.5);"><div style="color: #fff; font-weight: bold; font-size: 16px; text-transform: uppercase; letter-spacing: 1px;">TOTAL FILTRADO</div><div style="color: {c_t}; font-weight: bold; font-size: 20px;">${t_h:,.2f}</div></div>', unsafe_allow_html=True)

        st.markdown("<hr>", unsafe_allow_html=True)
        
        # --- CARGOS AUTOMÁTICOS ---
        with st.expander("Configurar Cargos Automáticos", expanded=False):            
            with st.form("form_nuevo_cargo_auto_nuevo", border=False):
                ca1, ca2, ca3 = st.columns([1.5, 1.5, 1])
                with ca1: c_auto_cta = st.selectbox("Cuenta Bancaria:", nombres_cuentas, key="auto_cta_n")
                with ca2: c_auto_cat = st.selectbox("Categoría afectada:", df_fijos["Categoría"].tolist() if not df_fijos.empty else [], key="auto_cat_n")
                with ca3: c_auto_dia = st.number_input("Día del cobro (1-31):", min_value=1, max_value=31, value=15, key="auto_dia_n")
      
                col_c1, col_c2 = st.columns([2, 1])
                with col_c1: c_auto_concepto = st.text_input("Concepto del Recibo:", key="auto_concepto_n")
                with col_c2: c_auto_monto = st.number_input("Monto a descontar ($):", min_value=0.0, step=100.0, key="auto_monto_n")
                
                if st.form_submit_button("Crear Cargo Automático", type="primary", use_container_width=True):
                    if c_auto_monto > 0 and c_auto_concepto:
                        nuevo_cargo = pd.DataFrame([{
                            "Concepto": c_auto_concepto, 
                            "Categoria": c_auto_cat, 
                            "Cuenta": c_auto_cta, 
                            "Monto": c_auto_monto, 
                            "Dia_Cobro": c_auto_dia, 
                            "Ultimo_Mes_Cobrado": "" 
                        }])
                        df_cargos_auto = pd.concat([df_cargos_auto, nuevo_cargo], ignore_index=True)
                        conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Cargos_Auto", data=df_cargos_auto)
                        st.session_state.df_cargos_auto = df_cargos_auto
                        st.success("✅ Cargo automático registrado.")
                        st.rerun()

            if not df_cargos_auto.empty:
                st.markdown("<br><h4 style='color: #4CAF50;'>Cargos Activos</h4>", unsafe_allow_html=True)
                for i, row in df_cargos_auto.iterrows():
                    if f"edit_auto_{i}" not in st.session_state: st.session_state[f"edit_auto_{i}"] = False

                    html_cargo = f'''
                    <div style="background: #1a1a1a; padding: 10px 15px; border-radius: 8px; border-left: 3px solid #1565C0; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <span style="color: #fff; font-weight: bold; font-size: 15px;">{row["Concepto"]}</span> <span style="color: #888; font-size: 12px;">({row["Categoria"]} - {row["Cuenta"]})</span><br>
                            <span style="color: #00E5FF; font-size: 12px; font-weight: bold;">Se cobra los días {row["Dia_Cobro"]}</span>
                        </div>
                        <span style="color: #F44336; font-weight: bold; font-size: 18px;">${float(row["Monto"]):,.2f}</span>
                    </div>
                    '''
                    ca_col1, ca_col2, ca_col3 = st.columns([6, 0.35, 0.35], gap="small")
                    with ca_col1: st.markdown(html_cargo, unsafe_allow_html=True)
                    with ca_col2: 
                        st.write("")
                        if st.button("✏️", key=f"btn_edit_{i}_n", help="Editar Cargo"):
                            st.session_state[f"edit_auto_{i}"] = not st.session_state[f"edit_auto_{i}"]
                            st.rerun()
                    with ca_col3:
                        st.write("") 
                        if st.button("🗑️", key=f"del_auto_{i}_n", help="Eliminar Cargo"):
                            df_cargos_auto = df_cargos_auto.drop(i)
                            conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Cargos_Auto", data=df_cargos_auto)
                            st.session_state.df_cargos_auto = df_cargos_auto
                            st.rerun()
                    
                    if st.session_state[f"edit_auto_{i}"]:
                        with st.container():
                            st.markdown("<div style='background: #262730; padding: 15px; border-radius: 10px; margin-bottom: 20px;'>", unsafe_allow_html=True)
                            ce1, ce2, ce3 = st.columns([2, 1, 1])
                            new_concepto = ce1.text_input("Concepto:", value=row["Concepto"], key=f"inp_con_{i}_n")
                            new_monto = ce2.number_input("Monto:", value=float(row["Monto"]), key=f"inp_mon_{i}_n")
                            new_dia = ce3.number_input("Día:", value=int(row["Dia_Cobro"]), min_value=1, max_value=31, key=f"inp_dia_{i}_n")
                            ce4, ce5 = st.columns(2)
                            new_cta = ce4.selectbox("Cuenta:", nombres_cuentas, index=nombres_cuentas.index(row["Cuenta"]) if row["Cuenta"] in nombres_cuentas else 0, key=f"inp_cta_{i}_n")
                            new_cat = ce5.selectbox("Categoría:", df_fijos["Categoría"].tolist(), index=df_fijos["Categoría"].tolist().index(row["Categoria"]) if row["Categoria"] in df_fijos["Categoría"].tolist() else 0, key=f"inp_cat_{i}_n")
                         
                            if st.button("💾 GUARDAR CAMBIOS", key=f"save_edit_{i}_n", use_container_width=True, type="primary"):
                                df_cargos_auto.at[i, "Concepto"] = new_concepto
                                df_cargos_auto.at[i, "Monto"] = new_monto
                                df_cargos_auto.at[i, "Dia_Cobro"] = new_dia
                                df_cargos_auto.at[i, "Cuenta"] = new_cta
                                df_cargos_auto.at[i, "Categoria"] = new_cat
                                conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Cargos_Auto", data=df_cargos_auto)
                                st.session_state.df_cargos_auto = df_cargos_auto
                                st.session_state[f"edit_auto_{i}"] = False
                                st.success("Cambios guardados.")
                                st.rerun()
                            st.markdown("</div>", unsafe_allow_html=True)

    mostrar_panel_pagos_unificado()

# ---------------------------------------------------------
# NUEVA SECCIÓN: TRADING (Inversiones y Retiros)
# ---------------------------------------------------------
with tab_trading:
    st.markdown("<h3 style='font-weight: 400; color: #FFFFFF;'>Gestión de Trading</h3>", unsafe_allow_html=True)
    
    # --- CÁLCULO SINCRONIZADO DE TRADING ---
    # 1. El dinero disponible SIEMPRE viene del sobre 'Inversion' de Gastos Fijos
    cap_disponible = 0.0
    if "Inversion" in df_fijos["Categoría"].values:
        idx_inv = df_fijos.index[df_fijos["Categoría"] == "Inversion"].tolist()[0]
        cap_disponible = float(df_fijos.at[idx_inv, "Fondo_Disponible"])

    # 2. Los otros totales sí vienen del historial de la hoja Trading
    cap_invertido = 0.0
    cap_retirado = 0.0
    if not df_trading.empty:
        df_trading["Monto"] = pd.to_numeric(df_trading["Monto"]).fillna(0)
        cap_invertido = df_trading[df_trading["Monto"] > 0]["Monto"].sum()
        # Ahora suma tanto los Retiros puros como cuando mueves dinero de vuelta al banco
        cap_retirado = abs(df_trading[df_trading["Tipo"].isin(["Retiro", "Mover Dinero"])]["Monto"].sum())

    # 3. Mostrar Métricas (Colores Rotados)
    col_k1, col_k2, col_k3 = st.columns(3)
    with col_k1:
        st.markdown(f"""<div style="background-color: #1a1a1a; padding: 15px; border-radius: 10px; border-left: 5px solid #4CAF50;">
            <p style="margin:0; color: #888; font-size: 11px;">FONDO DISPONIBLE</p>
            <h3 style="margin:0; color: #4CAF50;">${cap_disponible:,.2f}</h3></div>""", unsafe_allow_html=True)
    with col_k2:
        st.markdown(f"""<div style="background-color: #1a1a1a; padding: 15px; border-radius: 10px; border-left: 5px solid #F44336;">
            <p style="margin:0; color: #888; font-size: 11px;">TOTAL INVERTIDO</p>
            <h3 style="margin:0; color: #F44336;">${cap_invertido:,.2f}</h3></div>""", unsafe_allow_html=True)
    with col_k3:
        st.markdown(f"""<div style="background-color: #1a1a1a; padding: 15px; border-radius: 10px; border-left: 5px solid #F57C00;">
            <p style="margin:0; color: #888; font-size: 11px;">TOTAL RETIRADO</p>
            <h3 style="margin:0; color: #F57C00;">${cap_retirado:,.2f}</h3></div>""", unsafe_allow_html=True)
    st.write("")

# 🌟 FRAGMENTO PARA SINCRONIZAR SIN REDIBUJAR TODA LA APP 🌟
    @st.fragment
    def formulario_trading_dinamico():
        global df_trading, df_movs, df_cuentas, df_fijos
        
        col_t1, col_t2, col_t3, col_t4, col_t5 = st.columns([2, 2, 2, 1, 1])
        with col_t1: cta_t = st.selectbox("Cuenta Bancaria:", df_cuentas["Cuenta"].tolist() if not df_cuentas.empty else [])
 
        with col_t2: tipo_t = st.selectbox("Operación:", ["Inversión", "Retiro", "Mover Dinero"])
        
        with col_t3: 
            if tipo_t == "Mover Dinero":
                lista_c = ["Mover Dinero"]
            elif tipo_t == "Retiro":
                lista_c = ["Cuenta de fondeo"]
            else:
                lista_c = ["Trading View", "Cuenta de fondeo", "Fx Replay", "Mentoria", "OTRO"]
                
            c_sel_t = st.selectbox("Concepto:", lista_c)
            concepto_t = st.text_input("Escribe el concepto:") if c_sel_t == "OTRO" else c_sel_t
            
        with col_t4: monto_t = st.number_input("Monto ($):", min_value=0.0, step=100.0)
   
        with col_t5:
            st.write("") 
            btn_ejecutar = st.button("AGREGAR", use_container_width=True, type="primary")
            
        if btn_ejecutar:
            if monto_t > 0:
                if tipo_t == "Mover Dinero":
                    concepto_t = "Mover Dinero"
                elif c_sel_t == "Mover Dinero":
                    tipo_t = "Mover Dinero"

                monto_trading = monto_t if tipo_t == "Inversión" else -monto_t
                monto_banco = -monto_t if tipo_t == "Inversión" else monto_t
                fecha_actual = datetime.now().strftime("%Y-%m-%d")
                
                nueva_op = pd.DataFrame([{"Fecha": fecha_actual, "Cuenta": cta_t, "Tipo": tipo_t, "Concepto": concepto_t, "Monto": monto_trading}])
                df_trading = pd.concat([df_trading, nueva_op], ignore_index=True)
                
                nuevo_mov_gen = pd.DataFrame([{"Fecha": fecha_actual, "Cuenta": cta_t, "Concepto": f"TRADING: {concepto_t}", "Monto": monto_banco}])
                df_movs = pd.concat([df_movs, nuevo_mov_gen], ignore_index=True)
                
                idx_cta = df_cuentas.index[df_cuentas["Cuenta"] == cta_t].tolist()[0]
                df_cuentas.at[idx_cta, "Saldo"] = float(df_cuentas.at[idx_cta, "Saldo"]) + monto_banco
                
                # 🌟 MAGIA: Descontar de Inversión o alojar Retiros en "Inyección del trading" 🌟
                if tipo_t in ["Inversión", "Mover Dinero"] and "Inversion" in df_fijos["Categoría"].values:
                    idx_inv = df_fijos.index[df_fijos["Categoría"] == "Inversion"].tolist()[0]
                    df_fijos.at[idx_inv, "Fondo_Disponible"] = float(df_fijos.at[idx_inv, "Fondo_Disponible"]) - monto_t
                elif tipo_t == "Retiro":
                    cat_retiro = "Inyección del trading"
                    if cat_retiro in df_fijos["Categoría"].values:
                        idx_ret = df_fijos.index[df_fijos["Categoría"] == cat_retiro].tolist()[0]
                        df_fijos.at[idx_ret, "Fondo_Disponible"] = float(df_fijos.at[idx_ret, "Fondo_Disponible"]) + monto_t
                    else:
                        nueva_cat = pd.DataFrame([{"Categoría": cat_retiro, "Monto_Mensual": 0.0, "Fondo_Disponible": monto_t}])
                        df_fijos = pd.concat([df_fijos, nueva_cat], ignore_index=True)

                conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Trading", data=df_trading)
                conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Movimientos", data=df_movs)
                conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Cuentas", data=df_cuentas)
                conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
         
                st.session_state.df_trading = df_trading
                st.session_state.df_movs = df_movs
                st.session_state.df_cuentas = df_cuentas
                st.session_state.df_fijos = df_fijos
                
                st.success("Operación ejecutada y guardada al instante en todas las bases de datos.")
                st.rerun()

    formulario_trading_dinamico()
    if not df_trading.empty:
        st.markdown("---")
        st.markdown("<h4 style='color: #888; letter-spacing: 1px;'>📝 HISTORIAL</h4>", unsafe_allow_html=True)
        
        # --- SISTEMA DE FILTROS LINDOS (FRAGMENTADO PARA NO PARPADEAR) ---
        @st.fragment
        def mostrar_feed_trading():
            global df_trading, df_movs, df_cuentas, df_fijos
            
            # 🌟 Lógica Dinámica de Fechas para Trading 🌟
            opciones_tiempo_t = ["TODO"]
            meses_es_t = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
            
            if not df_trading.empty:
                df_temp_t = df_trading.copy()
                df_temp_t["Fecha_DT"] = pd.to_datetime(df_temp_t["Fecha"], errors='coerce')
                año_actual_t = datetime.now().year
                
                meses_datos_t = df_temp_t[df_temp_t["Fecha_DT"].dt.year == año_actual_t]["Fecha_DT"].dt.month.dropna().unique()
                opciones_tiempo_t += [meses_es_t[m] for m in sorted(meses_datos_t)]
                
                años_datos_t = df_temp_t["Fecha_DT"].dt.year.dropna().unique()
                opciones_tiempo_t += [str(int(a)) for a in sorted(años_datos_t, reverse=True) if a < año_actual_t]

            col_f1, col_f2, col_f3 = st.columns([1, 1, 1])
           
            with col_f1:
                f_tipo = st.selectbox("Filtrar", ["TODOS", "Inversión", "Retiro", "Mover Dinero", "Inyección Semanal"])
                
            with col_f2:
                if not df_trading.empty and "Concepto" in df_trading.columns:
                    conceptos_limpios = df_trading["Concepto"].dropna().astype(str).unique().tolist()
                    opciones_conceptos = ["TODOS"] + sorted(conceptos_limpios)
                else:
                    opciones_conceptos = ["TODOS"]
                f_concepto = st.selectbox("Concepto", opciones_conceptos)
                
            with col_f3:
                f_fecha_t = st.selectbox("Tiempo", opciones_tiempo_t, key="filtro_tiempo_trading")
            
            # Aplicar Filtros
            df_filtrado_t = df_trading.copy()
            
            # 🌟 Aplicar Filtro de Fechas Dinámico en Trading 🌟
            if not df_filtrado_t.empty and f_fecha_t != "TODO":
                df_filtrado_t["Fecha_DT"] = pd.to_datetime(df_filtrado_t["Fecha"], errors='coerce')
                if f_fecha_t in meses_es_t.values():
                    mes_num = list(meses_es_t.keys())[list(meses_es_t.values()).index(f_fecha_t)]
                    df_filtrado_t = df_filtrado_t[(df_filtrado_t["Fecha_DT"].dt.month == mes_num) & (df_filtrado_t["Fecha_DT"].dt.year == año_actual_t)]
                else: # Es un año pasado
                    df_filtrado_t = df_filtrado_t[df_filtrado_t["Fecha_DT"].dt.year == int(f_fecha_t)]
                    
                df_filtrado_t = df_filtrado_t.drop(columns=["Fecha_DT"])
            
            if f_tipo != "TODOS":
                df_filtrado_t = df_filtrado_t[df_filtrado_t["Tipo"] == f_tipo]
            if f_concepto != "TODOS":
                df_filtrado_t = df_filtrado_t[df_filtrado_t["Concepto"] == f_concepto]
            
            df_filtrado_t = df_filtrado_t.sort_index(ascending=False)

# Feed de tarjetas con Botón de Basura
            st.markdown('<div style="max-height: 500px; overflow-y: auto; padding-right: 10px; margin-top: 10px;">', unsafe_allow_html=True)
            
            for idx, row in df_filtrado_t.iterrows():
                monto = float(row["Monto"])
                color_op = "#F44336" if row["Tipo"] == "Inversión" else "#4CAF50"
                icon = "💸" if row["Tipo"] == "Inversión" else "💰"
                
                col_c1, col_edit, col_del = st.columns([6, 0.35, 0.35], gap="small")
                with col_c1:
                    tarjeta = f'<div style="background: linear-gradient(145deg, #1e1e1e, #121212); margin-bottom: 10px; padding: 15px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.03); display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 6px rgba(0,0,0,0.2);"><div style="display: flex; align-items: center; gap: 15px;"><div style="font-size: 24px;">{icon}</div><div><div style="color: #fff; font-weight: bold; font-size: 15px;">{row["Concepto"]}</div><div style="color: #666; font-size: 11px; text-transform: uppercase;">{row["Fecha"]} • {row["Cuenta"]}</div></div></div><div style="text-align: right;"><div style="color: {color_op}; font-weight: bold; font-size: 18px;">${abs(monto):,.2f}</div><div style="color: #444; font-size: 10px; font-weight: bold; text-transform: uppercase;">{row["Tipo"]}</div></div></div>'
                    st.markdown(tarjeta, unsafe_allow_html=True)
                with col_edit:
                    st.write("")
                    if st.button("✏️", key=f"btn_edit_{idx}", help="Editar Movimiento"):
                        st.session_state[f"edit_t_{idx}"] = not st.session_state.get(f"edit_t_{idx}", False)
                        st.session_state[f"conf_del_{idx}"] = False # Cierra la basura si estaba abierta
                with col_del:
                    st.write("")
                    if st.button("🗑️", key=f"del_{idx}", help="Borrar Movimiento"):
                        st.session_state[f"conf_del_{idx}"] = not st.session_state.get(f"conf_del_{idx}", False)
                        st.session_state[f"edit_t_{idx}"] = False # Cierra el lápiz si estaba abierto
                
                # --- LÓGICA DE BORRAR (Restaura todas las cuentas) ---
                if st.session_state.get(f"conf_del_{idx}", False):
                    st.warning("⚠️ ¿Seguro que deseas borrar? El dinero volverá a tus cuentas y fondos al instante.")
                    cy, cn = st.columns(2)
                    if cy.button("✅ Sí, Borrar", key=f"y_{idx}"):
                        cta_v, m_v, tipo_v, concepto_v = row["Cuenta"], float(row["Monto"]), row["Tipo"], row["Concepto"]
                        
                        # 1. Restaurar Banco (Matemática de signos corregida)
                        if cta_v in df_cuentas["Cuenta"].values:
                            idx_c = df_cuentas.index[df_cuentas["Cuenta"] == cta_v].tolist()[0]
                            if tipo_v == "Inversión":
                                df_cuentas.at[idx_c, "Saldo"] = float(df_cuentas.at[idx_c, "Saldo"]) + abs(m_v)
                            else: # Si fue Retiro o Mover Dinero, se lo quitamos al banco
                                df_cuentas.at[idx_c, "Saldo"] = float(df_cuentas.at[idx_c, "Saldo"]) - abs(m_v)
                        
                        # 2. Restaurar Fondo Disponible
                        if tipo_v in ["Inversión", "Mover Dinero"] and "Inversion" in df_fijos["Categoría"].values:
                            idx_i = df_fijos.index[df_fijos["Categoría"] == "Inversion"].tolist()[0]
                            df_fijos.at[idx_i, "Fondo_Disponible"] = float(df_fijos.at[idx_i, "Fondo_Disponible"]) + abs(m_v)
                        elif tipo_v == "Retiro" and "Inyección del trading" in df_fijos["Categoría"].values:
                            idx_r = df_fijos.index[df_fijos["Categoría"] == "Inyección del trading"].tolist()[0]
                            df_fijos.at[idx_r, "Fondo_Disponible"] = float(df_fijos.at[idx_r, "Fondo_Disponible"]) - abs(m_v)

                        # 3. Borrar del historial General
                        if not df_movs.empty:
                            mask_mov = (df_movs["Cuenta"] == cta_v) & (df_movs["Concepto"] == f"TRADING: {concepto_v}")
                            if mask_mov.any():
                                df_movs = df_movs.drop(df_movs[mask_mov].index[-1])

                        # 4. Borrar de Trading
                        df_trading = df_trading.drop(idx)
                        
                        conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Trading", data=df_trading)
                        conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Cuentas", data=df_cuentas)
                        conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
                        conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Movimientos", data=df_movs)
                        
                        st.session_state.df_trading, st.session_state.df_cuentas, st.session_state.df_fijos, st.session_state.df_movs = df_trading, df_cuentas, df_fijos, df_movs
                        st.session_state[f"conf_del_{idx}"] = False
                        st.rerun()
                        
                    if cn.button("❌ Cancelar", key=f"n_{idx}"):
                        st.session_state[f"conf_del_{idx}"] = False
                        st.rerun()

                # --- LÓGICA DE EDITAR (Ajusta saldos automáticamente) ---
                if st.session_state.get(f"edit_t_{idx}", False):
                    st.markdown("<div style='background: #262730; padding: 15px; border-radius: 10px; margin-bottom: 20px;'>", unsafe_allow_html=True)
                    ce1, ce2 = st.columns([2, 1])
                    new_concepto = ce1.text_input("Modificar Concepto:", value=row["Concepto"], key=f"in_con_{idx}")
                    new_monto = ce2.number_input("Modificar Monto:", value=float(abs(row["Monto"])), min_value=0.0, key=f"in_mon_{idx}")
                    
                    if st.button("💾 GUARDAR CAMBIOS", key=f"save_edit_{idx}", use_container_width=True, type="primary"):
                        cta_v, m_v_old, tipo_v = row["Cuenta"], float(row["Monto"]), row["Tipo"]
                        concepto_v_old = row["Concepto"]
                        
                        # A) Revertir la operación vieja matemáticamente para evitar descuadres
                        if cta_v in df_cuentas["Cuenta"].values:
                            idx_c = df_cuentas.index[df_cuentas["Cuenta"] == cta_v].tolist()[0]
                            if tipo_v == "Inversión":
                                df_cuentas.at[idx_c, "Saldo"] = float(df_cuentas.at[idx_c, "Saldo"]) + abs(m_v_old)
                            else: # Si fue Retiro o Mover Dinero
                                df_cuentas.at[idx_c, "Saldo"] = float(df_cuentas.at[idx_c, "Saldo"]) - abs(m_v_old)
                        
                        if tipo_v in ["Inversión", "Mover Dinero"] and "Inversion" in df_fijos["Categoría"].values:
                            idx_i = df_fijos.index[df_fijos["Categoría"] == "Inversion"].tolist()[0]
                            df_fijos.at[idx_i, "Fondo_Disponible"] = float(df_fijos.at[idx_i, "Fondo_Disponible"]) + abs(m_v_old)
                        elif tipo_v == "Retiro" and "Inyección del trading" in df_fijos["Categoría"].values:
                            idx_r = df_fijos.index[df_fijos["Categoría"] == "Inyección del trading"].tolist()[0]
                            df_fijos.at[idx_r, "Fondo_Disponible"] = float(df_fijos.at[idx_r, "Fondo_Disponible"]) - abs(m_v_old)

                        # B) Aplicar los valores nuevos
                        m_v_new = new_monto if tipo_v == "Inversión" else -new_monto
                        monto_banco_new = -new_monto if tipo_v == "Inversión" else new_monto
                        
                        if cta_v in df_cuentas["Cuenta"].values:
                            idx_c = df_cuentas.index[df_cuentas["Cuenta"] == cta_v].tolist()[0]
                            df_cuentas.at[idx_c, "Saldo"] = float(df_cuentas.at[idx_c, "Saldo"]) + monto_banco_new
                            
                        if tipo_v in ["Inversión", "Mover Dinero"] and "Inversion" in df_fijos["Categoría"].values:
                            idx_i = df_fijos.index[df_fijos["Categoría"] == "Inversion"].tolist()[0]
                            df_fijos.at[idx_i, "Fondo_Disponible"] = float(df_fijos.at[idx_i, "Fondo_Disponible"]) - new_monto
                        elif tipo_v == "Retiro" and "Inyección del trading" in df_fijos["Categoría"].values:
                            idx_r = df_fijos.index[df_fijos["Categoría"] == "Inyección del trading"].tolist()[0]
                            df_fijos.at[idx_r, "Fondo_Disponible"] = float(df_fijos.at[idx_r, "Fondo_Disponible"]) + new_monto

                        # C) Actualizar los textos y números en la base de datos
                        df_trading.at[idx, "Concepto"] = new_concepto
                        df_trading.at[idx, "Monto"] = m_v_new
                        
                        if not df_movs.empty:
                            mask_mov = (df_movs["Cuenta"] == cta_v) & (df_movs["Concepto"] == f"TRADING: {concepto_v_old}")
                            if mask_mov.any():
                                idx_mov_edit = df_movs[mask_mov].index[-1]
                                df_movs.at[idx_mov_edit, "Concepto"] = f"TRADING: {new_concepto}"
                                df_movs.at[idx_mov_edit, "Monto"] = monto_banco_new

                        # Guardar Todo
                        conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Trading", data=df_trading)
                        conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Cuentas", data=df_cuentas)
                        conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
                        conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Movimientos", data=df_movs)
                        
                        st.session_state.df_trading, st.session_state.df_cuentas, st.session_state.df_fijos, st.session_state.df_movs = df_trading, df_cuentas, df_fijos, df_movs
                        st.session_state[f"edit_t_{idx}"] = False
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                        
            st.markdown('</div>', unsafe_allow_html=True)

            # BALANCE FINAL
            total_inversiones = df_filtrado_t[df_filtrado_t["Tipo"] == "Inversión"]["Monto"].astype(float).sum()
            total_entradas = df_filtrado_t[df_filtrado_t["Tipo"].isin(["Retiro", "Mover Dinero", "Inyección Semanal"])]["Monto"].astype(float).abs().sum()
            balance_neto = total_entradas - total_inversiones
            
            color_t_t = "#4CAF50" if balance_neto >= 0 else "#F44336"
            signo_t_t = "+" if balance_neto > 0 else "-"
            
            st.markdown(f'<div style="background: linear-gradient(145deg, #121212, #0a0a0a); margin-top: 15px; padding: 15px; border-radius: 10px; border-top: 2px solid {color_t_t}; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 -4px 10px rgba(0,0,0,0.5);"><div style="color: #fff; font-weight: bold; font-size: 16px; text-transform: uppercase; letter-spacing: 1px;">BALANCE</div><div style="color: {color_t_t}; font-weight: bold; font-size: 20px;">{signo_t_t}${abs(balance_neto):,.2f}</div></div>', unsafe_allow_html=True)

        mostrar_feed_trading()

# ---------------------------------------------------------
# 4. CUENTAS (Cálculo Dinámico y Sobreescritura Forzada en Excel)
# ---------------------------------------------------------
with tab_cuentas:
    st.write("") 
    
    if not df_cuentas.empty and not df_fijos.empty:
        # 🌟 BALANCE TOTAL DINÁMICO
        fondos_limpios = df_fijos["Fondo_Disponible"].astype(str).str.replace("$", "", regex=False).str.replace(",", "", regex=False)
        t_total = pd.to_numeric(fondos_limpios, errors='coerce').fillna(0).sum()
        
        st.markdown(f"""
            <div style="background: linear-gradient(90deg, #0F2027 0%, #2C5364 100%); padding: 15px; border-radius: 12px; text-align: center; color: white; margin-bottom: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
                <p style="margin: 0; font-size: 11px; letter-spacing: 2px; color: #b0bec5; font-weight: 600;">BALANCE TOTAL DE FONDOS</p>
                <h1 style="margin: 0; font-size: 38px; font-weight: 700;">${t_total:,.2f}</h1>
            </div>
        """, unsafe_allow_html=True)
        
        cols = st.columns(4)
        colores_neon = ["#00E5FF", "#B388FF", "#FF8A80", "#69F0AE", "#FFD180", "#82B1FF"]
        
        hubo_cambios_en_excel = False # 🛡️ Control para no saturar la conexión a Google Sheets
        
        for i, (index, row) in enumerate(df_cuentas.iterrows()):
            # 1. Extraer categorías excluidas de esta cuenta
            excluidas = df_excep[df_excep["Cuenta"] == row['Cuenta']]["Categoria_Excluida"].tolist() if not df_excep.empty else []
            
            # 2. Filtrar y sumar sobres permitidos (El saldo real que la cuenta debería tener)
            cats_permitidas = df_fijos[~df_fijos["Categoría"].isin(excluidas)].copy()
            try:
                saldos_v = cats_permitidas["Fondo_Disponible"].astype(str).str.replace("$", "", regex=False).str.replace(",", "", regex=False)
                saldo_calculado = pd.to_numeric(saldos_v, errors='coerce').fillna(0).sum()
            except:
                saldo_calculado = 0.0
                
            # 3. Leer el saldo fijo y congelado que está actualmente en la base de datos
            try:
                saldo_viejo_excel = float(str(row['Saldo']).replace("$", "").replace(",", ""))
            except ValueError:
                saldo_viejo_excel = 0.0
                
            # 4. 🌟 LA MAGIA: Si el cálculo nuevo es diferente al Excel, modificamos los datos
            if round(saldo_viejo_excel, 2) != round(saldo_calculado, 2):
                df_cuentas.at[index, "Saldo"] = saldo_calculado
                hubo_cambios_en_excel = True

            # Dibujamos la tarjeta con el saldo correcto
            color_acento = colores_neon[i % len(colores_neon)]
            with cols[i % 4]:
                st.markdown(f"""
                    <div style="background: linear-gradient(145deg, #222, #111); padding: 20px; border-radius: 12px; border-top: 3px solid {color_acento}; margin-bottom: 15px; box-shadow: 0 8px 16px rgba(0,0,0,0.4), 0 0 12px {color_acento}30;">
                        <p style="margin: 0; font-size: 11px; text-transform: uppercase; font-weight: 700; color: #aaa; letter-spacing: 1px;">{row['Cuenta']}</p>
                        <h4 style="margin: 8px 0 0 0; font-size: 24px; font-weight: bold; color: #fff;">${saldo_calculado:,.2f}</h4>
                    </div>
                """, unsafe_allow_html=True)
                
        # 5. 🌟 SOBREESCRIBIR EXCEL FORZOSAMENTE 🌟
        # Si la app detectó que los valores fijos no cuadran con el cálculo, reescribe toda la hoja
        if hubo_cambios_en_excel:
            conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Cuentas", data=df_cuentas)
            st.session_state.df_cuentas = df_cuentas
    else:
        st.info("Aún no tienes cuentas registradas.")

    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Menú oculto en un expander para no ensuciar la pantalla
    with st.expander("Administrar Cuentas", expanded=False):
        col_e1, col_e2 = st.columns(2)
        
        with col_e1:
            st.markdown("<p style='color:#666; font-size:14px; margin-bottom:5px;'><b>Crear o Modificar</b></p>", unsafe_allow_html=True)
            opc = ["➕ NUEVA CUENTA"] + (df_cuentas["Cuenta"].tolist() if not df_cuentas.empty else [])
            c_edit = st.selectbox("Selecciona:", opc, label_visibility="collapsed")
            
            s_base = float(df_cuentas.loc[df_cuentas["Cuenta"] == c_edit, "Saldo"].values[0]) if c_edit != "➕ NUEVA CUENTA" else 0.0
            n_nombre = st.text_input("Nombre de la cuenta:", placeholder="Ej: Efectivo") if c_edit == "➕ NUEVA CUENTA" else c_edit
            n_saldo = st.number_input("Saldo Actual:", value=s_base, step=100.0)
            
            if st.button("Guardar Cambios", use_container_width=True):
                if n_nombre:
                    if not df_cuentas.empty and n_nombre in df_cuentas["Cuenta"].values:
                        df_cuentas.loc[df_cuentas["Cuenta"] == n_nombre, "Saldo"] = n_saldo
                    else:
                        df_cuentas = pd.concat([df_cuentas, pd.DataFrame([{"Cuenta": n_nombre, "Saldo": n_saldo}])], ignore_index=True)
                    conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Cuentas", data=df_cuentas)
                    st.cache_data.clear()
                    st.rerun()

        with col_e2:
            st.markdown("<p style='color:#666; font-size:14px; margin-bottom:5px;'><b>Eliminar Cuenta</b></p>", unsafe_allow_html=True)
            if not df_cuentas.empty:
                c_del = st.selectbox("Borrar:", df_cuentas["Cuenta"].tolist(), label_visibility="collapsed")
                st.write("") # Espaciador
                st.write("") # Espaciador
                if st.button("Eliminar Permanentemente", use_container_width=True):
                    df_cuentas = df_cuentas[df_cuentas["Cuenta"] != c_del]
                    conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Cuentas", data=df_cuentas)
                    st.cache_data.clear()
                    st.rerun()