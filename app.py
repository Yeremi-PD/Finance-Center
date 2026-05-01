import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import base64
import streamlit.components.v1 as components

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

st.set_page_config(page_title="Finanzas Master Pro", page_icon=logo_final, layout="wide")
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
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        margin-top: 0rem !important;
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
                "Trading": ["Fecha", "Cuenta", "Tipo", "Concepto", "Monto"]
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

# Usamos las variables de la sesión para que todo sea instantáneo
df_fijos = st.session_state.df_fijos
df_movs = st.session_state.df_movs
df_cuentas = st.session_state.df_cuentas
df_excep = st.session_state.df_excep
df_trading = st.session_state.df_trading # Nueva hoja cargada


# --- NAVEGACIÓN CON PESTAÑAS ESTILO BOTONES PREMIUM (INSTANTÁNEO) ---
st.markdown("<h1 style='text-align: center; color: #4CAF50; margin-bottom: 0px;'>💰 MY FINANCIAL CENTER</h1>", unsafe_allow_html=True)

st.markdown("""
<style>
    /* 1. Contenedor general de las pestañas (MÁS ESPACIO PARA QUE NO SE CORTE) */
    div[data-testid="stTabs"] {
        padding: 25px 0px 20px 0px !important; 
        margin-top: 5px !important;
    }

    /* 2. Estilizar cada pestaña individualmente para simular un botón */
    div[data-testid="stTabs"] button {
        font-size: 18px !important; 
        font-weight: 700 !important;
        background-color: rgba(40, 40, 40, 0.6) !important; 
        border-radius: 12px !important; 
        padding: 12px 24px !important;
        margin: 0px 8px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.5), inset 0px 1px 1px rgba(255,255,255,0.1) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        color: #d1d1d1 !important;
        overflow: visible !important; /* Clave para que no se corte el sombreado */
    }

    /* 4. Efecto Hover: Cuando pasas el mouse */
    div[data-testid="stTabs"] button:hover {
        transform: translateY(-5px) !important; /* Levanta el botón un poco más */
        box-shadow: 0px 10px 20px rgba(76, 175, 80, 0.4) !important; 
        border-color: #4CAF50 !important;
        color: #ffffff !important;
        z-index: 10 !important; /* Asegura que pase por encima del texto de arriba */
    }

    /* 5. Estilo de la pestaña seleccionada (ACTIVA) */
    div[data-testid="stTabs"] button[aria-selected="true"] {
        background: linear-gradient(145deg, #4CAF50, #2E7D32) !important; 
        color: white !important;
        box-shadow: 0px 0px 20px rgba(76, 175, 80, 0.6) !important; 
        border: none !important;
        transform: scale(1.05) translateY(-2px) !important; 
        z-index: 10 !important;
    }

    /* 6. Limpieza visual */
    div[data-testid="stTabs"] [data-baseweb="tab-highlight-point"] {
        display: none !important; 
    }
    div[data-baseweb="tab-list"] {
        gap: 12px !important;
        border-bottom: none !important; 
        justify-content: center !important; 
        padding-top: 15px !important; /* Da aire para el salto */
        padding-bottom: 15px !important; /* Da aire para la sombra */
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
    st.subheader("⚙️ Configurar Gastos Fijos")
    
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
                # ACTUALIZAR MEMORIA LOCAL PARA QUE EL BALANCE CAMBIE AL INSTANTE
                st.session_state.df_fijos = df_fijos 
                st.rerun()
        with col_btn2:
            if st.button("🗑️", help="Eliminar Categoría", use_container_width=True):
                if not df_fijos.empty and cat_sel in df_fijos["Categoría"].values:
                    df_fijos = df_fijos[df_fijos["Categoría"] != cat_sel]
                    conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
                    st.cache_data.clear()
                    st.rerun()

    st.markdown("---")
    if not df_fijos.empty:
        df_order = df_fijos.copy()
        df_order["Monto Semanal"] = pd.to_numeric(df_order["Monto_Mensual"]) / 4
        df_order["Monto Anual"] = pd.to_numeric(df_order["Monto_Mensual"]) * 12
        df_order["Fondo_Disponible"] = pd.to_numeric(df_order["Fondo_Disponible"])
        
# Orden pedido: Semanal, Mensual, Anual, Fondo
        df_order = df_order[["Categoría", "Monto Semanal", "Monto_Mensual", "Monto Anual", "Fondo_Disponible"]]
        
        # 🌟 DISEÑO DE TARJETAS INDIVIDUALES (CERO TABLAS) 🌟
        html_gastos = '<div style="display: flex; flex-wrap: wrap; gap: 15px; margin-top: 15px;">'
        
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
                
            color_fondo_txt = "#4CAF50" if fondo >= 0 else "#F44336"
            
            # Tarjeta tipo Widget (Todo en una línea para que Streamlit no lo rompa)
            html_gastos += f'<div style="background: linear-gradient(145deg, #2a2a2a, #1a1a1a); border-top: 4px solid #1565C0; padding: 15px; border-radius: 10px; flex: 1 1 calc(25% - 15px); min-width: 200px; box-shadow: 0 4px 8px rgba(0,0,0,0.3);"><h4 style="margin: 0 0 12px 0; color: #fff; text-align: center; font-size: 18px; letter-spacing: 1px;">{row["Categoría"]}</h4><div style="display: flex; justify-content: space-between; margin-bottom: 6px;"><span style="color: #888; font-size: 13px;">Semanal:</span><span style="color: #ddd; font-weight: bold; font-size: 14px;">${semanal:,.0f}</span></div><div style="display: flex; justify-content: space-between; margin-bottom: 6px;"><span style="color: #888; font-size: 13px;">Mensual:</span><span style="color: #ddd; font-weight: bold; font-size: 14px;">${mensual:,.0f}</span></div><div style="display: flex; justify-content: space-between; margin-bottom: 6px;"><span style="color: #888; font-size: 13px;">Anual:</span><span style="color: #ddd; font-weight: bold; font-size: 14px;">${anual:,.0f}</span></div><hr style="border: 0; border-top: 1px solid rgba(255,255,255,0.1); margin: 10px 0;"><div style="display: flex; justify-content: space-between; align-items: center;"><span style="color: #aaa; font-size: 13px; font-weight: bold;">Fondo Actual:</span><span style="color: {color_fondo_txt}; font-weight: bold; font-size: 18px;">${fondo:,.0f}</span></div></div>'
            
        html_gastos += '</div>'
        st.markdown(html_gastos, unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. PAGOS Y EXCEPCIONES (Filtro Maestro por Cuenta)
# ---------------------------------------------------------
with tab_pagos:
    # 🌟 TODO EL PANEL UNIFICADO EN UN FRAGMENTO PARA EVITAR PARPADEOS 🌟
    @st.fragment
    def mostrar_panel_pagos_unificado():
        # Conectamos con la memoria global de la app
        global df_fijos, df_movs, df_cuentas, df_excep
        
        st.markdown("<h2 style='color: #1565C0;'>💸 Gestión de Fondos y Gastos</h2>", unsafe_allow_html=True)
        
        col_i1, col_i3 = st.columns([1.5, 1])
        nombres_cuentas = df_cuentas["Cuenta"].tolist() if not df_cuentas.empty else []
        
        with col_i1:
            opciones_inyec = ["TODAS"] + nombres_cuentas
            # Este es el FILTRO MAESTRO: Todo lo que veas abajo será de esta cuenta
            cuenta_maestra = st.selectbox("📥 Seleccionar Cuenta (Filtro Maestro):", opciones_inyec)
            
            if cuenta_maestra != "TODAS":
                # Mostramos las excepciones solo de la cuenta seleccionada
                exc_c = df_excep[df_excep["Cuenta"] == cuenta_maestra]["Categoria_Excluida"].tolist() if not df_excep.empty else []
                categorias_v = df_fijos["Categoría"].tolist() if not df_fijos.empty else []
                exc_c_v = [cat for cat in exc_c if cat in categorias_v]
                
                with st.form("form_excepciones", border=False):
                    nuevas_exc = st.multiselect(f"Excluir categorías en {cuenta_maestra}:", categorias_v, default=exc_c_v)
                    btn_guardar_exc = st.form_submit_button("💾 Guardar en Excel")
                    
                if btn_guardar_exc:
                    # Leemos lo que hay en el Excel actualmente
                    df_temp = conn.read(spreadsheet=URL_GOOGLE_SHEET, worksheet="Excepciones", ttl=0).dropna(how="all")
                    # Quitamos lo viejo de ESTA cuenta para no duplicar
                    if not df_temp.empty:
                        df_temp = df_temp[df_temp["Cuenta"] != cuenta_maestra]
                    
                    # Creamos las nuevas filas asegurando que diga la cuenta
                    nuevas_rows = pd.DataFrame([{"Cuenta": cuenta_maestra, "Categoria_Excluida": x} for x in nuevas_exc])
                    df_final_excep = pd.concat([df_temp, nuevas_rows], ignore_index=True)
                    
                    # GUARDADO TOTAL: Excel + Memoria Local
                    conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Excepciones", data=df_final_excep)
                    st.session_state.df_excep = df_final_excep # Esto evita el reseteo
                    st.success(f"Configuración de {cuenta_maestra} guardada en Excel.")
                    st.rerun()

        with col_i3:
            st.write("")
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if st.button("➕ SEMANA", use_container_width=True, type="primary"):
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
                        
                        nuevo_m = pd.DataFrame([{"Fecha": datetime.now().strftime("%Y-%m-%d"), "Cuenta": cta, "Concepto": "INYECCIÓN SEMANAL", "Monto": monto_inyec}])
                        df_movs = pd.concat([df_movs, nuevo_m], ignore_index=True)

                    conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
                    conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Cuentas", data=df_cuentas)
                    conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Movimientos", data=df_movs)
                    st.session_state.df_fijos, st.session_state.df_cuentas, st.session_state.df_movs = df_fijos, df_cuentas, df_movs
                    st.rerun()
            
            with col_b2:
                if st.button("↩️ DESHACER", use_container_width=True):
                    if not df_movs.empty and "INYECCIÓN SEMANAL" in df_movs["Concepto"].values:
                        ult_f = df_movs[df_movs["Concepto"] == "INYECCIÓN SEMANAL"]["Fecha"].iloc[-1]
                        a_revertir = df_movs[(df_movs["Concepto"] == "INYECCIÓN SEMANAL") & (df_movs["Fecha"] == ult_f)]
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
                        conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
                        conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Cuentas", data=df_cuentas)
                        conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Movimientos", data=df_movs)
                        st.session_state.df_fijos, st.session_state.df_cuentas, st.session_state.df_movs = df_fijos, df_cuentas, df_movs
                        st.rerun()

        st.markdown("<hr>", unsafe_allow_html=True)
        
        # --- FORMULARIO DE GASTO ---
        with st.form("form_gasto_unificado", border=False):
            cg1, cg2, cg3, cg4 = st.columns([1.5, 1.5, 1, 1.2])
            with cg1: c_gasto = st.selectbox("💳 Cuenta:", nombres_cuentas, index=nombres_cuentas.index(cuenta_maestra) if cuenta_maestra in nombres_cuentas else 0)
            with cg2: 
                l_n_g = df_excep[df_excep["Cuenta"] == c_gasto]["Categoria_Excluida"].tolist() if not df_excep.empty else []
                s_gasto = st.selectbox("📂 Categoría:", df_fijos[~df_fijos["Categoría"].isin(l_n_g)]["Categoría"].tolist() if not df_fijos.empty else [])
            with cg3: m_gasto = st.number_input("💲 Monto:", min_value=0.0)
            with cg4: 
                st.write("")
                if st.form_submit_button("APLICAR GASTO", use_container_width=True, type="primary"):
                    if m_gasto > 0:
                        nuevo_m = pd.DataFrame([{"Fecha": datetime.now().strftime("%Y-%m-%d"), "Cuenta": c_gasto, "Concepto": s_gasto, "Monto": -m_gasto}])
                        df_movs = pd.concat([df_movs, nuevo_m], ignore_index=True)
                        idx_f = df_fijos.index[df_fijos["Categoría"] == s_gasto].tolist()[0]
                        df_fijos.at[idx_f, "Fondo_Disponible"] = float(df_fijos.at[idx_f, "Fondo_Disponible"]) - m_gasto
                        conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Movimientos", data=df_movs)
                        conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
                        st.session_state.df_movs, st.session_state.df_fijos = df_movs, df_fijos
                        st.rerun()

        # --- DINERO Y HISTORIAL (SOLO DE LA CUENTA SELECCIONADA) ---
        cf1, cf2 = st.columns([1.5, 2])
        with cf1:
            st.markdown(f"<h4 style='color: #2E7D32;'>💰 Disponible: {cuenta_maestra}</h4>", unsafe_allow_html=True)
            l_n_v = df_excep[df_excep["Cuenta"] == cuenta_maestra]["Categoria_Excluida"].tolist() if (not df_excep.empty and cuenta_maestra != "TODAS") else []
            df_sobres = df_fijos[~df_fijos["Categoría"].isin(l_n_v)]
            html_s = '<div style="display: flex; flex-wrap: wrap; gap: 10px;">'
            for _, r in df_sobres.iterrows():
                f = float(str(r["Fondo_Disponible"]).replace("$", "").replace(",", ""))
                c = "#4CAF50" if f >= 0 else "#F44336"
                html_s += f'<div style="background: #1a1a1a; border-left: 4px solid {c}; padding: 10px; border-radius: 8px; flex: 1 1 calc(50% - 10px); display: flex; justify-content: space-between;"><span style="font-size: 13px;">{r["Categoría"]}</span><span style="color: {c}; font-weight: bold;">${f:,.0f}</span></div>'
            st.markdown(html_s + '</div>', unsafe_allow_html=True)

        with cf2:
            st.markdown(f"<h4 style='color: #1565C0;'>📜 Historial: {cuenta_maestra}</h4>", unsafe_allow_html=True)
            df_h = df_movs.copy()
            if cuenta_maestra != "TODAS": df_h = df_h[df_h["Cuenta"] == cuenta_maestra]
            f_cat = st.selectbox("Filtrar por Categoría:", ["VER TODO"] + df_fijos["Categoría"].tolist())
            if f_cat != "VER TODO": df_h = df_h[df_h["Concepto"] == f_cat]
            df_h = df_h.sort_index(ascending=False)
            
            html_hist = '<div style="max-height: 350px; overflow-y: auto;">'
            for _, r in df_h.iterrows():
                m = float(r["Monto"])
                color = "#4CAF50" if m >= 0 else "#F44336"
                html_hist += f'<div style="background: #1e1e1e; margin-bottom: 5px; padding: 10px; border-radius: 5px; display: flex; justify-content: space-between;"><div><div style="font-size: 13px; font-weight: bold;">{r["Concepto"]}</div><div style="font-size: 10px; color: #888;">{r["Fecha"]} • {r["Cuenta"]}</div></div><div style="color: {color}; font-weight: bold;">${m:,.2f}</div></div>'
            
            t_h = df_h["Monto"].sum()
            c_t = "#4CAF50" if t_h >= 0 else "#F44336"
            html_hist += f'</div><div style="background: linear-gradient(145deg, #121212, #0a0a0a); margin-top: 15px; padding: 15px; border-radius: 8px; border-top: 2px solid {c_t}; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 -4px 10px rgba(0,0,0,0.5);"><div style="color: #fff; font-weight: bold; font-size: 16px; text-transform: uppercase; letter-spacing: 1px;">TOTAL FILTRADO</div><div style="color: {c_t}; font-weight: bold; font-size: 20px;">${t_h:,.2f}</div></div>'
            st.markdown(html_hist, unsafe_allow_html=True)
            
            if st.button("🗑️ BORRAR ÚLTIMO", use_container_width=True):
                if not df_movs.empty:
                    ult = df_movs.iloc[-1]
                    cta_m, conc_m, m_m = ult["Cuenta"], ult["Concepto"], float(ult["Monto"])
                    if conc_m in df_fijos["Categoría"].values:
                        idx_f = df_fijos.index[df_fijos["Categoría"] == conc_m].tolist()[0]
                        df_fijos.at[idx_f, "Fondo_Disponible"] = float(df_fijos.at[idx_f, "Fondo_Disponible"]) - m_m
                    if cta_m in df_cuentas["Cuenta"].values:
                        idx_c = df_cuentas.index[df_cuentas["Cuenta"] == cta_m].tolist()[0]
                        df_cuentas.at[idx_c, "Saldo"] = float(df_cuentas.at[idx_c, "Saldo"]) - m_m
                    df_movs = df_movs.drop(df_movs.index[-1])
                    conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
                    conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Cuentas", data=df_cuentas)
                    conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Movimientos", data=df_movs)
                    st.session_state.df_fijos, st.session_state.df_cuentas, st.session_state.df_movs = df_fijos, df_cuentas, df_movs
                    st.rerun()

    mostrar_panel_pagos_unificado()

# ---------------------------------------------------------
# NUEVA SECCIÓN: TRADING (Inversiones y Retiros)
# ---------------------------------------------------------
with tab_trading:
    st.markdown("<h3 style='font-weight: 400; color: #555;'>📈 Gestión de Trading</h3>", unsafe_allow_html=True)
    
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
        cap_retirado = abs(df_trading[df_trading["Monto"] < 0]["Monto"].sum())

    # 3. Mostrar Métricas (Colores Rotados)
    col_k1, col_k2, col_k3 = st.columns(3)
    with col_k1:
        # Ahora es VERDE (Traído de "Enviado")
        st.markdown(f"""<div style="background-color: #1a1a1a; padding: 15px; border-radius: 10px; border-left: 5px solid #4CAF50;">
            <p style="margin:0; color: #888; font-size: 11px;">FONDO DISPONIBLE</p>
            <h3 style="margin:0; color: #4CAF50;">${cap_disponible:,.2f}</h3></div>""", unsafe_allow_html=True)
    with col_k2:
        # Ahora es ROJO (Traído de "Retirado")
        st.markdown(f"""<div style="background-color: #1a1a1a; padding: 15px; border-radius: 10px; border-left: 5px solid #F44336;">
            <p style="margin:0; color: #888; font-size: 11px;">TOTAL INVERTIDO</p>
            <h3 style="margin:0; color: #F44336;">${cap_invertido:,.2f}</h3></div>""", unsafe_allow_html=True)
    with col_k3:
        # Ahora es NARANJA (Traído de "Fondo")
        st.markdown(f"""<div style="background-color: #1a1a1a; padding: 15px; border-radius: 10px; border-left: 5px solid #F57C00;">
            <p style="margin:0; color: #888; font-size: 11px;">TOTAL RETIRADO</p>
            <h3 style="margin:0; color: #F57C00;">${cap_retirado:,.2f}</h3></div>""", unsafe_allow_html=True)
    st.write("")

# 🌟 FORMULARIO CERRADO PARA EVITAR REDIBUJO AUTOMÁTICO 🌟
    with st.form("formulario_ejecutar_trading", border=False):
        col_t1, col_t2, col_t3, col_t4, col_t5 = st.columns([2, 2, 2, 1, 1])
        with col_t1: cta_t = st.selectbox("Cuenta Bancaria:", df_cuentas["Cuenta"].tolist() if not df_cuentas.empty else [])
        with col_t2: tipo_t = st.selectbox("Operación:", ["Inversión", "Retiro"])
        with col_t3: 
            lista_c = ["Trading View", "Cuenta de fondeo", "Fx Replay", "Mentoria", "OTRO"]
            c_sel_t = st.selectbox("Concepto:", lista_c)
            concepto_t = st.text_input("Escribe el concepto:") if c_sel_t == "OTRO" else c_sel_t
        with col_t4: monto_t = st.number_input("Monto ($):", min_value=0.0, step=100.0)
        with col_t5:
            st.write("") # Espaciador para alinear el botón
            # El botón de formulario detiene las recargas hasta que haces clic
            btn_ejecutar = st.form_submit_button("AGREGAR", use_container_width=True, type="primary")
        
    if btn_ejecutar:
        if monto_t > 0:
            monto_trading = monto_t if tipo_t == "Inversión" else -monto_t
            monto_banco = -monto_t if tipo_t == "Inversión" else monto_t
            fecha_actual = datetime.now().strftime("%Y-%m-%d")
            
            # 1. Preparar datos de Trading e Historial General
            nueva_op = pd.DataFrame([{"Fecha": fecha_actual, "Cuenta": cta_t, "Tipo": tipo_t, "Concepto": concepto_t, "Monto": monto_trading}])
            df_trading = pd.concat([df_trading, nueva_op], ignore_index=True)
            
            nuevo_mov_gen = pd.DataFrame([{"Fecha": fecha_actual, "Cuenta": cta_t, "Concepto": f"TRADING: {concepto_t}", "Monto": monto_banco}])
            df_movs = pd.concat([df_movs, nuevo_mov_gen], ignore_index=True)
            
            # 2. Actualizar Saldo de la Cuenta Bancaria
            idx_cta = df_cuentas.index[df_cuentas["Cuenta"] == cta_t].tolist()[0]
            df_cuentas.at[idx_cta, "Saldo"] = float(df_cuentas.at[idx_cta, "Saldo"]) + monto_banco
            
            # 3. Si es Inversión, descontar del sobre "Inversion"
            if tipo_t == "Inversión" and "Inversion" in df_fijos["Categoría"].values:
                idx_inv = df_fijos.index[df_fijos["Categoría"] == "Inversion"].tolist()[0]
                df_fijos.at[idx_inv, "Fondo_Disponible"] = float(df_fijos.at[idx_inv, "Fondo_Disponible"]) - monto_t

            # 4. GUARDADO MASIVO INMEDIATO EN GOOGLE SHEETS
            conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Trading", data=df_trading)
            conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Movimientos", data=df_movs)
            conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Cuentas", data=df_cuentas)
            conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
            
            # 5. Actualizar la memoria de la sesión local para reflejar al instante
            st.session_state.df_trading = df_trading
            st.session_state.df_movs = df_movs
            st.session_state.df_cuentas = df_cuentas
            st.session_state.df_fijos = df_fijos
            
            st.success("Operación ejecutada y guardada al instante en todas las bases de datos.")
            st.rerun()

    if not df_trading.empty:
        st.markdown("---")
        st.markdown("<h4 style='color: #888; letter-spacing: 1px;'>📝 HISTORIAL DE MOVIMIENTOS</h4>", unsafe_allow_html=True)
        
# --- SISTEMA DE FILTROS LINDOS (FRAGMENTADO PARA NO PARPADEAR) ---
        @st.fragment
        def mostrar_feed_trading():
            # 🛡️ SOLUCIÓN AL ERROR DE MEMORIA (UnboundLocalError) 🛡️
            global df_trading, df_movs, df_cuentas, df_fijos
            
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                f_tipo = st.selectbox("Filtrar por Operación:", ["TODOS", "Inversión", "Retiro"])
            with col_f2:
                # 🛡️ ESCUDO ANTI-ERRORES DEFINITIVO PARA STREAMLIT CLOUD 🌟
                if not df_trading.empty and "Concepto" in df_trading.columns:
                    conceptos_limpios = df_trading["Concepto"].dropna().astype(str).unique().tolist()
                    opciones_conceptos = ["TODOS"] + sorted(conceptos_limpios)
                else:
                    opciones_conceptos = ["TODOS"]
                    
                f_concepto = st.selectbox("Filtrar por Concepto:", opciones_conceptos)
            
            # Aplicar Filtros
            df_filtrado_t = df_trading.copy()
            if f_tipo != "TODOS":
                df_filtrado_t = df_filtrado_t[df_filtrado_t["Tipo"] == f_tipo]
            if f_concepto != "TODOS":
                df_filtrado_t = df_filtrado_t[df_filtrado_t["Concepto"] == f_concepto]
            
            df_filtrado_t = df_filtrado_t.sort_index(ascending=False)

            # Feed de tarjetas
            html_feed_t = '<div style="max-height: 500px; overflow-y: auto; padding-right: 10px; margin-top: 10px;">'
            for _, row in df_filtrado_t.iterrows():
                monto = float(row["Monto"])
                color_op = "#F44336" if row["Tipo"] == "Inversión" else "#4CAF50"
                icon = MAPA_EMOJIS.get(row["Concepto"], "🚀" if row["Tipo"] == "Inversión" else "💰")
                
                tarjeta = f'<div style="background: linear-gradient(145deg, #1e1e1e, #121212); margin-bottom: 10px; padding: 15px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.03); display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 6px rgba(0,0,0,0.2);"><div style="display: flex; align-items: center; gap: 15px;"><div style="font-size: 24px;">{icon}</div><div><div style="color: #fff; font-weight: bold; font-size: 15px;">{row["Concepto"]}</div><div style="color: #666; font-size: 11px; text-transform: uppercase;">{row["Fecha"]} • {row["Cuenta"]}</div></div></div><div style="text-align: right;"><div style="color: {color_op}; font-weight: bold; font-size: 18px;">${abs(monto):,.2f}</div><div style="color: #444; font-size: 10px; font-weight: bold; text-transform: uppercase;">{row["Tipo"]}</div></div></div>'
                html_feed_t += tarjeta
                
            # 🌟 NUEVO CÁLCULO DEL TOTAL TRADING (INVERSIÓN = NEGATIVO, RETIRO = POSITIVO) 🌟
            total_inversiones = df_filtrado_t[df_filtrado_t["Tipo"] == "Inversión"]["Monto"].astype(float).sum()
            total_retiros = df_filtrado_t[df_filtrado_t["Tipo"] == "Retiro"]["Monto"].astype(float).abs().sum() # Forzamos a positivo por si acaso
            
            # La matemática del Trader: Lo que saqué menos lo que metí
            balance_neto = total_retiros - total_inversiones
            
            color_t_t = "#4CAF50" if balance_neto >= 0 else "#F44336"
            signo_t_t = "+" if balance_neto > 0 else "-"
            
            html_feed_t += f'<div style="background: linear-gradient(145deg, #121212, #0a0a0a); margin-top: 15px; padding: 15px; border-radius: 10px; border-top: 2px solid {color_t_t}; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 -4px 10px rgba(0,0,0,0.5);"><div style="color: #fff; font-weight: bold; font-size: 16px; text-transform: uppercase; letter-spacing: 1px;">BALANCE</div><div style="color: {color_t_t}; font-weight: bold; font-size: 20px;">{signo_t_t}${abs(balance_neto):,.2f}</div></div>'
            html_feed_t += '</div>'
            st.markdown(html_feed_t, unsafe_allow_html=True)

            # 🌟 BOTÓN DE ELIMINACIÓN CON REVERSIÓN TOTAL 🌟
            if st.button("🗑️ ELIMINAR ÚLTIMO MOVIMIENTO DE TRADING", use_container_width=True):
                if not df_trading.empty:
                    # 1. Obtener datos del último movimiento de trading
                    ult_t = df_trading.iloc[-1]
                    cta_t = ult_t["Cuenta"]
                    tipo_t = ult_t["Tipo"]
                    monto_t = float(ult_t["Monto"])
                    concepto_t = ult_t["Concepto"]

                    # 2. Revertir Saldo en Cuenta Bancaria
                    # Si fue Inversión (monto_t > 0), en el banco se restó. Lo sumamos.
                    # Si fue Retiro (monto_t < 0), en el banco se sumó. Lo restamos.
                    monto_a_revertir_banco = monto_t if tipo_t == "Inversión" else -abs(monto_t)
                    
                    if cta_t in df_cuentas["Cuenta"].values:
                        idx_c = df_cuentas.index[df_cuentas["Cuenta"] == cta_t].tolist()[0]
                        df_cuentas.at[idx_c, "Saldo"] = float(df_cuentas.at[idx_c, "Saldo"]) + monto_a_revertir_banco
                    
                    # 3. Revertir sobre de "Inversion" en Gastos Fijos (Solo si fue Inversión)
                    if tipo_t == "Inversión" and "Inversion" in df_fijos["Categoría"].values:
                        idx_inv = df_fijos.index[df_fijos["Categoría"] == "Inversion"].tolist()[0]
                        # Devolvemos el monto al sobre
                        df_fijos.at[idx_inv, "Fondo_Disponible"] = float(df_fijos.at[idx_inv, "Fondo_Disponible"]) + abs(monto_t)

                    # 4. Eliminar del Historial General (df_movs)
                    # Buscamos el registro que coincida con este movimiento de trading
                    if not df_movs.empty:
                        concepto_buscado = f"TRADING: {concepto_t}"
                        mask_mov = (df_movs["Cuenta"] == cta_t) & (df_movs["Concepto"] == concepto_buscado)
                        if mask_mov.any():
                            # Borramos la última coincidencia encontrada
                            idx_mov_borrar = df_movs[mask_mov].index[-1]
                            df_movs = df_movs.drop(idx_mov_borrar)

                    # 5. Eliminar del Historial de Trading
                    df_trading = df_trading.drop(df_trading.index[-1])

                    # 6. Actualización Masiva (Sheets y Sesión)
                    conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Trading", data=df_trading)
                    conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Cuentas", data=df_cuentas)
                    conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
                    conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Movimientos", data=df_movs)
                    
                    st.session_state.df_trading = df_trading
                    st.session_state.df_cuentas = df_cuentas
                    st.session_state.df_fijos = df_fijos
                    st.session_state.df_movs = df_movs
                    
                    st.success("Movimiento de Trading eliminado. Dinero devuelto a la cuenta y al sobre de inversión.")
                    st.rerun()
            
        mostrar_feed_trading()

        # --- PANEL OCULTO PARA ADMINISTRACIÓN (Edición/Borrado) ---
        with st.expander("🛠️ Editar Historial"):
            df_edit_t = df_trading.copy()
            if "Fecha" in df_edit_t.columns:
                df_edit_t["Fecha"] = pd.to_datetime(df_edit_t["Fecha"]).dt.date
            df_edit_t["Monto"] = pd.to_numeric(df_edit_t["Monto"], errors='coerce').fillna(0.0)
            df_edit_t["🗑️"] = False
            
            edited_df_t = st.data_editor(
                df_edit_t, use_container_width=True, hide_index=True,
                column_config={
                    "🗑️": st.column_config.CheckboxColumn("Borrar", width="small"),
                    "Monto": st.column_config.NumberColumn("Monto ($)", format="$%.2f"),
                    "Tipo": st.column_config.SelectboxColumn("Operación", options=["Inversión", "Retiro"]),
                }
            )
            
            if st.button("💾 CONFIRMAR", type="primary"):
                # Reversión y Aplicación (Lógica de balances que ya tenías)
                for _, fila_v in st.session_state.df_trading.iterrows():
                    cta_v, m_v, tipo_v = fila_v["Cuenta"], float(fila_v["Monto"]), fila_v["Tipo"]
                    if cta_v in df_cuentas["Cuenta"].values:
                        idx_c = df_cuentas.index[df_cuentas["Cuenta"] == cta_v].tolist()[0]
                        df_cuentas.at[idx_c, "Saldo"] = float(df_cuentas.at[idx_c, "Saldo"]) - (m_v if tipo_v == "Retiro" else -abs(m_v))
                    if tipo_v == "Inversión" and "Inversion" in df_fijos["Categoría"].values:
                        idx_i = df_fijos.index[df_fijos["Categoría"] == "Inversion"].tolist()[0]
                        df_fijos.at[idx_i, "Fondo_Disponible"] = float(df_fijos.at[idx_i, "Fondo_Disponible"]) + abs(m_v)

                df_final_t = edited_df_t[edited_df_t["🗑️"] == False].drop(columns=["🗑️"])
                for _, fila_n in df_final_t.iterrows():
                    cta_n, m_n, tipo_n = fila_n["Cuenta"], float(fila_n["Monto"]), fila_n["Tipo"]
                    if cta_n in df_cuentas["Cuenta"].values:
                        idx_c = df_cuentas.index[df_cuentas["Cuenta"] == cta_n].tolist()[0]
                        df_cuentas.at[idx_c, "Saldo"] = float(df_cuentas.at[idx_c, "Saldo"]) + (m_n if tipo_n == "Retiro" else -abs(m_n))
                    if tipo_n == "Inversión" and "Inversion" in df_fijos["Categoría"].values:
                        idx_i = df_fijos.index[df_fijos["Categoría"] == "Inversion"].tolist()[0]
                        df_fijos.at[idx_i, "Fondo_Disponible"] = float(df_fijos.at[idx_i, "Fondo_Disponible"]) - abs(m_n)

                if "Fecha" in df_final_t.columns: df_final_t["Fecha"] = df_final_t["Fecha"].astype(str)
                conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Trading", data=df_final_t)
                conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Cuentas", data=df_cuentas)
                conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
                st.session_state.df_trading, st.session_state.df_cuentas, st.session_state.df_fijos = df_final_t, df_cuentas, df_fijos
                st.success("¡Historial actualizado!")
                st.rerun()

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
    with st.expander("⚙️ Administrar Cuentas", expanded=False):
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