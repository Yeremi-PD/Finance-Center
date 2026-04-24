import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Mis Finanzas", page_icon="💰", layout="wide")

CATEGORIAS = [
    "Gasolina", "Pa La Se", "Bebe", "Elect", "Gas", "Agua", 
    "Gym", "Deuda", "Subs", "Pelo", "Otros", "Inversion", "Ahorro", "Disfrute"
]

# --- CONEXIÓN A GOOGLE SHEETS ---
# Pega aquí la URL de tu Google Sheet
URL_GOOGLE_SHEET = "https://docs.google.com/spreadsheets/d/1lswvfo2ggmqvyslLCYj-WWpO56v0jgV0dVpNwXnEuDY/edit?gid=0#gid=0"

# Establecer conexión
conn = st.connection("gsheets", type=GSheetsConnection)

# Función para cargar datos desde Sheets
def cargar_datos():
    # Leemos las primeras 4 columnas
    df = conn.read(spreadsheet=URL_GOOGLE_SHEET, usecols=[0, 1, 2, 3])
    # Limpiamos filas que estén completamente vacías
    df = df.dropna(how="all")
    return df

df = cargar_datos()

st.title("📊 Dashboard de Mis Finanzas (Conectado a Google Sheets)")
st.markdown("---")

with st.sidebar:
    st.header("➕ Nuevo Registro")
    fecha = st.date_input("Fecha")
    categoria = st.selectbox("Categoría", CATEGORIAS)
    monto = st.number_input("Monto ($)", min_value=0.0, format="%.2f")
    descripcion = st.text_input("Descripción (Opcional)")
    
    if st.button("Guardar Registro", type="primary"):
        # Crear el nuevo registro
        nuevo_registro = pd.DataFrame([{
            "Fecha": fecha.strftime("%Y-%m-%d"), 
            "Categoría": categoria, 
            "Monto": float(monto), 
            "Descripción": descripcion
        }])
        
        # Unir lo viejo con lo nuevo
        df_actualizado = pd.concat([df, nuevo_registro], ignore_index=True)
        
        # Sobreescribir el Google Sheet con los datos actualizados
        conn.update(spreadsheet=URL_GOOGLE_SHEET, data=df_actualizado)
        
        st.success("¡Guardado en Google Sheets! 🚀")
        st.cache_data.clear() # Limpiar la memoria para forzar la recarga
        st.rerun()

if not df.empty:
    # Asegurarnos de que el monto sea un número para poder sumarlo
    df['Monto'] = pd.to_numeric(df['Monto'], errors='coerce').fillna(0)
    
    total_gastos = df["Monto"].sum()
    st.metric(label="Total Registrado", value=f"${total_gastos:,.2f}")
    
    st.markdown("### Resumen Gráfico")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        gastos_cat = df.groupby("Categoría")["Monto"].sum().reset_index()
        fig_pie = px.pie(gastos_cat, values="Monto", names="Categoría", 
                         title="Distribución por Categoría", hole=0.4,
                         color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with col2:
        st.markdown("**Historial Detallado**")
        st.dataframe(df.sort_values(by="Fecha", ascending=False), use_container_width=True, hide_index=True)
else:
    st.info("👋 Tu Google Sheet está vacío. ¡Empieza a agregar gastos!")
