import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# 1. Configuración de página
st.set_page_config(page_title="Mi Centro Financiero", page_icon="🏦", layout="wide")

# URL de tu Google Sheet (la misma que ya tienes)
URL_GOOGLE_SHEET = "https://docs.google.com/spreadsheets/d/1lswvfo2ggmqvyslLCYj-WWpO56v0jgV0dVpNwXnEuDY/edit#gid=0"

# Conexión
conn = st.connection("gsheets", type=GSheetsConnection)

# --- ESTILO DE NAVEGACIÓN SUPERIOR ---
# Creamos una tira de botones arriba
st.markdown("### 🛠️ Menú de Control")
col_nav1, col_nav2, col_nav3 = st.columns(3)

# Usamos session_state para saber en qué página estamos
if 'pagina' not in st.session_state:
    st.session_state.pagina = 'Dashboard'

if col_nav1.button("📊 Gastos Diarios", use_container_width=True):
    st.session_state.pagina = 'Dashboard'
if col_nav2.button("📌 Gastos Fijos", use_container_width=True):
    st.session_state.pagina = 'Gastos Fijos'
if col_nav3.button("💳 Dinero en Cuentas", use_container_width=True):
    st.session_state.pagina = 'Cuentas'

st.markdown("---")

# --- LÓGICA DE PÁGINAS ---

# ---------------------------------------------------------
# PÁGINA 1: DASHBOARD DE GASTOS DIARIOS
# ---------------------------------------------------------
if st.session_state.pagina == 'Dashboard':
    st.header("Historial de Gastos")
    
    # Cargar datos de la pestaña "Registros"
    df = conn.read(spreadsheet=URL_GOOGLE_SHEET, worksheet="Registros")
    df = df.dropna(how="all")

    with st.sidebar:
        st.subheader("Añadir Gasto Diario")
        f_fecha = st.date_input("Fecha")
        f_cat = st.selectbox("Categoría", ["Gasolina", "Pa La Se", "Bebe", "Elect", "Gas", "Agua", "Gym", "Deuda", "Subs", "Pelo", "Otros", "Inversion", "Ahorro", "Disfrute"])
        f_monto = st.number_input("Monto ($)", min_value=0.0)
        f_desc = st.text_input("Nota")
        
        if st.button("Guardar Gasto"):
            nuevo = pd.DataFrame([{"Fecha": str(f_fecha), "Categoría": f_cat, "Monto": f_monto, "Descripción": f_desc}])
            df_up = pd.concat([df, nuevo], ignore_index=True)
            conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Registros", data=df_up)
            st.success("¡Guardado!")
            st.rerun()

    if not df.empty:
        df['Monto'] = pd.to_numeric(df['Monto'], errors='coerce').fillna(0)
        st.metric("Total Gastado", f"${df['Monto'].sum():,.2f}")
        fig = px.pie(df, values='Monto', names='Categoría', hole=0.4, title="Reparto de Gastos")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df, use_container_width=True)

# ---------------------------------------------------------
# PÁGINA 2: GASTOS FIJOS (Se mantienen fijos)
# ---------------------------------------------------------
elif st.session_state.pagina == 'Gastos Fijos':
    st.header("📌 Gastos Fijos Mensuales")
    st.info("Aquí pones lo que pagas siempre (Renta, Internet, etc.)")
    
    # Cargar de la pestaña "Gastos_Fijos"
    df_fijos = conn.read(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos")
    df_fijos = df_fijos.dropna(how="all")

    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Nuevo Gasto Fijo")
        fijo_nombre = st.text_input("Servicio/Gasto")
        fijo_monto = st.number_input("Monto Mensual ($)", min_value=0.0)
        fijo_dia = st.number_input("Día de cobro", 1, 31)
        
        if st.button("Agregar a Fijos"):
            nuevo_fijo = pd.DataFrame([{"Gasto": fijo_nombre, "Monto": fijo_monto, "Vencimiento": fijo_dia}])
            df_fijos_up = pd.concat([df_fijos, nuevo_fijo], ignore_index=True)
            conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos_up)
            st.rerun()

    with col2:
        st.dataframe(df_fijos, use_container_width=True, hide_index=True)
        total_fijo = df_fijos["Monto"].sum() if not df_fijos.empty else 0
        st.subheader(f"Total Fijo Mensual: ${total_fijo:,.2f}")

# ---------------------------------------------------------
# PÁGINA 3: DINERO EN CUENTAS
# ---------------------------------------------------------
elif st.session_state.pagina == 'Cuentas':
    st.header("💳 Dinero en Cuentas y Bancos")
    
    df_cuentas = conn.read(spreadsheet=URL_GOOGLE_SHEET, worksheet="Cuentas")
    df_cuentas = df_cuentas.dropna(how="all")

    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Actualizar Saldo")
        banco = st.text_input("Nombre del Banco/Cuenta")
        saldo = st.number_input("Saldo Actual ($)", min_value=0.0)
        
        if st.button("Actualizar Cuenta"):
            # Si el banco ya existe, lo actualizamos, si no, lo añadimos
            if not df_cuentas.empty and banco in df_cuentas["Banco/Cuenta"].values:
                df_cuentas.loc[df_cuentas["Banco/Cuenta"] == banco, "Saldo_Actual"] = saldo
            else:
                nueva_cta = pd.DataFrame([{"Banco/Cuenta": banco, "Saldo_Actual": saldo}])
                df_cuentas = pd.concat([df_cuentas, nueva_cta], ignore_index=True)
            
            conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Cuentas", data=df_cuentas)
            st.rerun()

    with col2:
        st.table(df_cuentas)
        gran_total = df_cuentas["Saldo_Actual"].sum() if not df_cuentas.empty else 0
        st.success(f"### Dinero Total Disponible: ${gran_total:,.2f}")