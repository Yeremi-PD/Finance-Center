import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 1. Configuración de la página (para que se vea ancha y bonita)
st.set_page_config(page_title="Mis Finanzas", page_icon="💰", layout="wide")

# 2. Las categorías de tu imagen
CATEGORIAS = [
    "Gasolina", "Pa La Se", "Bebe", "Elect", "Gas", "Agua", 
    "Gym", "Deuda", "Subs", "Pelo", "Otros", "Inversion", "Ahorro", "Disfrute"
]

ARCHIVO_CSV = "mis_datos_finanzas.csv"

# 3. Función para cargar y guardar datos
def cargar_datos():
    if os.path.exists(ARCHIVO_CSV):
        return pd.read_csv(ARCHIVO_CSV)
    else:
        return pd.DataFrame(columns=["Fecha", "Categoría", "Monto", "Descripción"])

def guardar_datos(df):
    df.to_csv(ARCHIVO_CSV, index=False)

df = cargar_datos()

# 4. Título Principal
st.title("📊 Dashboard de Mis Finanzas")
st.markdown("---")

# 5. BARRA LATERAL (Sidebar) para ingresar datos
with st.sidebar:
    st.header("➕ Nuevo Registro")
    fecha = st.date_input("Fecha")
    categoria = st.selectbox("Categoría", CATEGORIAS)
    monto = st.number_input("Monto ($)", min_value=0.0, format="%.2f")
    descripcion = st.text_input("Descripción (Opcional)")
    
    if st.button("Guardar Registro", type="primary"):
        nuevo_registro = pd.DataFrame([{
            "Fecha": fecha, 
            "Categoría": categoria, 
            "Monto": monto, 
            "Descripción": descripcion
        }])
        df = pd.concat([df, nuevo_registro], ignore_index=True)
        guardar_datos(df)
        st.success("¡Guardado correctamente!")
        st.rerun() # Recarga la página para mostrar los datos nuevos

# 6. PANEL PRINCIPAL (Dashboard)
if not df.empty:
    # Fila de métricas
    total_gastos = df["Monto"].sum()
    st.metric(label="Total Registrado", value=f"${total_gastos:,.2f}")
    
    st.markdown("### Resumen Gráfico")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Gráfico de pastel súper bonito usando Plotly
        gastos_cat = df.groupby("Categoría")["Monto"].sum().reset_index()
        fig_pie = px.pie(gastos_cat, values="Monto", names="Categoría", 
                         title="Distribución por Categoría", hole=0.4,
                         color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with col2:
        # Tabla con el historial
        st.markdown("**Historial Detallado**")
        st.dataframe(df.sort_values(by="Fecha", ascending=False), use_container_width=True, hide_index=True)
        
        # OJO: Botón vital para descargar tu información
        st.markdown("<br>", unsafe_allow_html=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar mis datos (Backup CSV)",
            data=csv,
            file_name='backup_mis_finanzas.csv',
            mime='text/csv',
        )
else:
    st.info("👋 ¡Hola! Tu dashboard está vacío. Usa el menú de la izquierda para agregar tu primer gasto.")
