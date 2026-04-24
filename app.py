import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. Configuración de pantalla completa
st.set_page_config(page_title="Mi Presupuesto Maestro", page_icon="🏦", layout="wide")

# URL de tu Google Sheet
URL_GOOGLE_SHEET = "https://docs.google.com/spreadsheets/d/1lswvfo2ggmqvyslLCYj-WWpO56v0jgV0dVpNwXnEuDY/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

# Categorías
CATEGORIAS = [
    "Gasolina", "Pa La Se", "Bebe", "Elect", "Gas", "Agua", 
    "Gym", "Deuda", "Subs", "Pelo", "Otros", "Inversion", "Ahorro", "Disfrute", "Seguro"
]

MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

# --- NAVEGACIÓN SUPERIOR (Sin menú lateral) ---
st.markdown("### 🏦 SISTEMA DE CONTROL FINANCIERO")
col_nav1, col_nav2 = st.columns([1, 1])

if 'seccion' not in st.session_state:
    st.session_state.seccion = 'Vista'

with col_nav1:
    if st.button("📊 VER MI PRESUPUESTO ANUAL", use_container_width=True):
        st.session_state.seccion = 'Vista'
with col_nav2:
    if st.button("⚙️ AJUSTAR MONTOS MENSUALES", use_container_width=True):
        st.session_state.seccion = 'Ajustes'

st.markdown("---")

# Cargar datos desde Google Sheets
df_fijos = conn.read(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos")
df_fijos = df_fijos.dropna(how="all")

# ---------------------------------------------------------
# SECCIÓN: AJUSTES (Aquí metes los datos ahora)
# ---------------------------------------------------------
if st.session_state.seccion == 'Ajustes':
    st.subheader("⚙️ Configuración de Gastos Fijos")
    st.write("Selecciona una categoría y pon cuánto pagas al mes. Se guardará para todo el año.")
    
    col_a, col_b, col_c = st.columns([2, 2, 1])
    
    with col_a:
        cat_sel = st.selectbox("Categoría a modificar", CATEGORIAS)
    with col_b:
        monto_sel = st.number_input("Monto Mensual ($)", min_value=0.0, step=100.0)
    with col_c:
        st.write(" ") # Espacio
        if st.button("💾 GUARDAR", use_container_width=True, type="primary"):
            if not df_fijos.empty and "Categoría" in df_fijos.columns and cat_sel in df_fijos["Categoría"].values:
                df_fijos.loc[df_fijos["Categoría"] == cat_sel, "Monto_Mensual"] = monto_sel
            else:
                nuevo = pd.DataFrame([{"Categoría": cat_sel, "Monto_Mensual": monto_sel}])
                df_fijos = pd.concat([df_fijos, nuevo], ignore_index=True)
            
            conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
            st.cache_data.clear()
            st.success(f"¡{cat_sel} actualizado!")
            st.rerun()

    st.markdown("---")
    st.write("**Tus montos actuales guardados:**")
    st.table(df_fijos)

# ---------------------------------------------------------
# SECCIÓN: VISTA (La tabla grande tipo imagen)
# ---------------------------------------------------------
elif st.session_state.seccion == 'Vista':
    if not df_fijos.empty and "Monto_Mensual" in df_fijos.columns:
        df_fijos["Monto_Mensual"] = pd.to_numeric(df_fijos["Monto_Mensual"], errors="coerce").fillna(0)
        
        # 1. Tabla de Resumen Rápido
        st.subheader("📋 Resumen de Costos")
        df_res = df_fijos.copy()
        df_res["Semana"] = df_res["Monto_Mensual"] / 4
        df_res["Año"] = df_res["Monto_Mensual"] * 12
        
        res_display = df_res.set_index("Categoría")[["Semana", "Monto_Mensual", "Año"]].T
        res_display.index = ["Semanal", "Mensual", "Anual"]
        st.dataframe(res_display.style.format("{:,.0f}"), use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # 2. La Gran Tabla de Proyección de 12 Meses
        st.subheader("📅 Proyección Mensual Detallada")
        
        # Creamos la tabla con los meses como FILAS y categorías como COLUMNAS
        df_anual = pd.DataFrame(index=MESES, columns=df_fijos["Categoría"].tolist())
        
        for cat in df_fijos["Categoría"]:
            monto = df_fijos.loc[df_fijos["Categoría"] == cat, "Monto_Mensual"].values[0]
            df_anual[cat] = monto
            
        # Fila de totales al final (como la barra verde de tu foto)
        df_anual.loc["🟢 TOTAL ACUMULADO"] = df_anual.sum()
        
        # Aplicamos estilo para que se vea limpio
        st.dataframe(df_anual.style.format("{:,.0f}"), use_container_width=True)
        
    else:
        st.warning("⚠️ No hay datos. Haz clic en el botón 'AJUSTAR MONTOS MENSUALES' para empezar.")