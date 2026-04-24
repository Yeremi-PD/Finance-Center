import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. Configuración
st.set_page_config(page_title="Mi Centro Financiero", page_icon="💰", layout="wide")

URL_GOOGLE_SHEET = "https://docs.google.com/spreadsheets/d/1lswvfo2ggmqvyslLCYj-WWpO56v0jgV0dVpNwXnEuDY/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

# Categorías y Meses
CATEGORIAS = ["Gasolina", "Pa La Se", "Bebe", "Elect", "Gas", "Agua", "Gym", "Deuda", "Subs", "Pelo", "Otros", "Inversion", "Ahorro", "Disfrute", "Seguro"]
MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

# --- NAVEGACIÓN SUPERIOR ---
st.markdown("### 🏦 GESTIÓN DE FINANZAS PRO")
col_nav1, col_nav2, col_nav3 = st.columns(3)

if 'seccion' not in st.session_state:
    st.session_state.seccion = 'Vista'

with col_nav1:
    if st.button("📊 PRESUPUESTO ANUAL", use_container_width=True):
        st.session_state.seccion = 'Vista'
with col_nav2:
    if st.button("⚙️ CONFIGURAR GASTOS", use_container_width=True):
        st.session_state.seccion = 'Ajustes'
with col_nav3:
    if st.button("💸 PAGOS Y SALDO", use_container_width=True):
        st.session_state.seccion = 'Pagos'

st.markdown("---")

# Cargar Datos
df_fijos = conn.read(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos").dropna(how="all")
df_movs = conn.read(spreadsheet=URL_GOOGLE_SHEET, worksheet="Movimientos").dropna(how="all")

# ---------------------------------------------------------
# SECCIÓN 1: VISTA (Tabla Proyectada)
# ---------------------------------------------------------
if st.session_state.seccion == 'Vista':
    if not df_fijos.empty:
        st.subheader("📅 Proyección Mensual de Gastos Fijos")
        df_anual = pd.DataFrame(index=MESES, columns=df_fijos["Categoría"].tolist())
        for cat in df_fijos["Categoría"]:
            monto = df_fijos.loc[df_fijos["Categoría"] == cat, "Monto_Mensual"].values[0]
            df_anual[cat] = monto
        df_anual.loc["🟢 TOTAL ACUMULADO"] = df_anual.sum()
        st.dataframe(df_anual.style.format("{:,.0f}"), use_container_width=True)
    else:
        st.warning("Ve a 'CONFIGURAR GASTOS' para empezar.")

# ---------------------------------------------------------
# SECCIÓN 2: AJUSTES (Configurar montos)
# ---------------------------------------------------------
elif st.session_state.seccion == 'Ajustes':
    st.subheader("⚙️ Ajuste de Montos Mensuales")
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1: cat_sel = st.selectbox("Categoría", CATEGORIAS)
    with c2: monto_sel = st.number_input("Monto Mensual ($)", min_value=0.0)
    with c3:
        st.write("")
        if st.button("GUARDAR", use_container_width=True, type="primary"):
            if not df_fijos.empty and cat_sel in df_fijos["Categoría"].values:
                df_fijos.loc[df_fijos["Categoría"] == cat_sel, "Monto_Mensual"] = monto_sel
            else:
                nuevo = pd.DataFrame([{"Categoría": cat_sel, "Monto_Mensual": monto_sel}])
                df_fijos = pd.concat([df_fijos, nuevo], ignore_index=True)
            conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
            st.cache_data.clear()
            st.rerun()
    st.table(df_fijos)

# ---------------------------------------------------------
# SECCIÓN 3: PAGOS Y SALDO (¡La nueva caja de descuentos!)
# ---------------------------------------------------------
elif st.session_state.seccion == 'Pagos':
    st.subheader("💸 Control de Saldo y Pagos")
    
    # Calcular saldo actual
    saldo_total = df_movs["Monto"].sum() if not df_movs.empty else 0
    
    # Mostrar el saldo en grande
    color_saldo = "normal" if saldo_total >= 0 else "inverse"
    st.metric(label="DINERO DISPONIBLE EN CUENTA", value=f"${saldo_total:,.2f}", delta=None)

    st.markdown("---")
    st.write("### Registrar Nuevo Movimiento")
    st.info("Para restar dinero, pon el número en negativo (ejemplo: -500). Para sumar (sueldo), ponlo positivo.")
    
    col_p1, col_p2, col_p3 = st.columns([2, 2, 1])
    with col_p1: concepto = st.text_input("Concepto (ej: Pago de Luz o Sueldo)")
    with col_p2: monto_pago = st.number_input("Monto ($)", format="%.2f")
    with col_p3:
        st.write("")
        if st.button("REGISTRAR", use_container_width=True, type="primary"):
            nuevo_mov = pd.DataFrame([{"Concepto": concepto, "Monto": monto_pago}])
            df_movs = pd.concat([df_movs, nuevo_mov], ignore_index=True)
            conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Movimientos", data=df_movs)
            st.cache_data.clear()
            st.success("Movimiento registrado")
            st.rerun()

    st.markdown("### Historial de Movimientos")
    st.dataframe(df_movs.sort_index(ascending=False), use_container_width=True, hide_index=True)