import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Configuración
st.set_page_config(page_title="Mi Presupuesto Fijo", page_icon="🏦", layout="wide")

URL_GOOGLE_SHEET = "https://docs.google.com/spreadsheets/d/1lswvfo2ggmqvyslLCYj-WWpO56v0jgV0dVpNwXnEuDY/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

# Categorías basadas en tu imagen
CATEGORIAS = [
    "Gasolina", "Pa La Se", "Bebe", "Elect", "Gas", "Agua", 
    "Gym", "Deuda", "Subs", "Pelo", "Otros", "Inversion", "Ahorro", "Disfrute", "Seguro"
]

st.title("📌 Dashboard de Presupuesto Fijo")
st.markdown("---")

# Cargar datos
df_fijos = conn.read(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos")
df_fijos = df_fijos.dropna(how="all")

# Sidebar para ingresar los montos fijos
with st.sidebar:
    st.header("⚙️ Ingresar Presupuesto")
    st.write("Agrega cuánto gastas al MES en cada cosa:")
    cat_sel = st.selectbox("Categoría", CATEGORIAS)
    monto_sel = st.number_input("Monto por Mes ($)", min_value=0.0, step=100.0)
    
    if st.button("Guardar / Actualizar ☁️", type="primary"):
        # Si la categoría ya está, actualiza el valor. Si no, la añade.
        if not df_fijos.empty and "Categoría" in df_fijos.columns and cat_sel in df_fijos["Categoría"].values:
            df_fijos.loc[df_fijos["Categoría"] == cat_sel, "Monto_Mensual"] = monto_sel
        else:
            nuevo = pd.DataFrame([{"Categoría": cat_sel, "Monto_Mensual": monto_sel}])
            df_fijos = pd.concat([df_fijos, nuevo], ignore_index=True)
            
        conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
        st.cache_data.clear()
        st.rerun()

# --- MOSTRAR LAS TABLAS ---
if not df_fijos.empty and "Monto_Mensual" in df_fijos.columns:
    df_fijos["Monto_Mensual"] = pd.to_numeric(df_fijos["Monto_Mensual"], errors="coerce").fillna(0)
    
    st.subheader("💡 Resumen: Gasto por Semana, Mes y Año")
    # Cálculos
    df_resumen = df_fijos.copy()
    df_resumen["Gasto Semanal"] = df_resumen["Monto_Mensual"] / 4
    df_resumen["Gasto Anual"] = df_resumen["Monto_Mensual"] * 12
    
    # Transformamos la tabla para que las categorías sean columnas (como querías)
    df_display = df_resumen.set_index("Categoría")[["Gasto Semanal", "Monto_Mensual", "Gasto Anual"]].T
    df_display.index = ["🗓️ Por Semana", "📅 Por Mes", "🌎 Por Año"]
    
    # Agregamos una columna al final que sume todos tus gastos juntos
    df_display["TOTAL GENERAL"] = df_display.sum(axis=1)
    
    # Mostrar tabla con formato de dinero
    st.dataframe(df_display.style.format("{:,.2f}"), use_container_width=True)
    
    st.markdown("---")
    
    st.subheader("📊 Proyección Anual (12 Meses)")
    st.info("Esta tabla es exactamente igual a la de tu imagen.")
    
    # Creamos la cuadrícula de 12 meses
    meses = [f"Mes {i}" for i in range(1, 13)]
    df_12 = pd.DataFrame(index=meses, columns=df_fijos["Categoría"].tolist())
    
    # Llenamos la tabla con el monto mensual
    for cat in df_fijos["Categoría"]:
        monto = df_fijos.loc[df_fijos["Categoría"] == cat, "Monto_Mensual"].values[0]
        df_12[cat] = monto
        
    # Agregamos la fila de Total Anual al fondo (como la barra verde de tu foto)
    df_12.loc["TOTAL ANUAL"] = df_12.sum()
    
    st.dataframe(df_12.style.format("{:,.2f}"), use_container_width=True)

else:
    st.info("👈 ¡Bienvenido! Tu tabla está vacía. Usa el menú de la izquierda para agregar cuánto gastas al mes en 'Gasolina', 'Agua', etc. La tabla se generará sola.")