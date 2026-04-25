import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Finanzas Master Pro", page_icon="💳", layout="wide")

URL_GOOGLE_SHEET = "https://docs.google.com/spreadsheets/d/1lswvfo2ggmqvyslLCYj-WWpO56v0jgV0dVpNwXnEuDY/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

CATEGORIAS_BASE = ["Gasolina", "Pa La Se", "Bebe", "Elect", "Gas", "Agua", "Gym", "Deuda", "Subs", "Pelo", "Otros", "Inversion", "Ahorro", "Disfrute", "Seguro"]
MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

# --- CARGAR DATOS ---
def cargar_hoja(nombre):
    try:
        return conn.read(spreadsheet=URL_GOOGLE_SHEET, worksheet=nombre).dropna(how="all")
    except:
        return pd.DataFrame()

df_fijos = cargar_hoja("Gastos_Fijos")
df_movs = cargar_hoja("Movimientos")
df_cuentas = cargar_hoja("Cuentas")
df_excep = cargar_hoja("Excepciones") # Nueva hoja para excepciones por cuenta

# Asegurar columnas
if not df_fijos.empty and "Fondo_Disponible" not in df_fijos.columns:
    df_fijos["Fondo_Disponible"] = 0.0

# --- NAVEGACIÓN ---
st.markdown("<h1 style='text-align: center; color: #4CAF50;'>💰 MI CENTRO FINANCIERO</h1>", unsafe_allow_html=True)
col_n1, col_n2, col_n3, col_n4 = st.columns(4)

if 'seccion' not in st.session_state: st.session_state.seccion = 'Vista'

with col_n1:
    if st.button("📊 PROYECCIÓN ANUAL", use_container_width=True): st.session_state.seccion = 'Vista'
with col_n2:
    if st.button("⚙️ GASTOS FIJOS", use_container_width=True): st.session_state.seccion = 'Ajustes'
with col_n3:
    if st.button("💸 REGISTRAR GASTOS", use_container_width=True): st.session_state.seccion = 'Pagos'
with col_n4:
    if st.button("💳 MIS CUENTAS", use_container_width=True): st.session_state.seccion = 'Cuentas'
st.markdown("---")

# ---------------------------------------------------------
# 1. VISTA: PROYECCIÓN ANUAL (INTERFAZ BELLA)
# ---------------------------------------------------------
if st.session_state.seccion == 'Vista':
    if not df_fijos.empty:
        # Métricas principales
        df_fijos["Monto_Mensual"] = pd.to_numeric(df_fijos["Monto_Mensual"]).fillna(0)
        total_m = df_fijos["Monto_Mensual"].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Presupuesto Mensual", f"${total_m:,.0f}")
        c2.metric("Inyección Semanal Necesaria", f"${total_m/4:,.0f}")
        c3.metric("Proyección Anual", f"${total_m*12:,.0f}")

        st.write("")
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            fig1 = px.pie(df_fijos, values='Monto_Mensual', names='Categoría', hole=0.5, title="Reparto por Categoría")
            st.plotly_chart(fig1, use_container_width=True)
        with col_g2:
            fig2 = px.bar(df_fijos, x='Categoría', y='Monto_Mensual', title="Presupuesto por Categoría", color='Categoría')
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("#### 🗓️ Tabla de Proyección a 12 Meses")
        df_anual = pd.DataFrame(index=MESES, columns=df_fijos["Categoría"].tolist())
        for cat in df_fijos["Categoría"]:
            monto = df_fijos.loc[df_fijos["Categoría"] == cat, "Monto_Mensual"].values[0]
            df_anual[cat] = monto
        df_anual["TOTAL MES"] = df_anual.sum(axis=1)
        df_anual.loc["TOTAL ANUAL"] = df_anual.sum()
        
        st.dataframe(df_anual.style.format("{:,.0f}").background_gradient(cmap="Blues", axis=None), 
                     use_container_width=True, height=550)

# ---------------------------------------------------------
# 2. AJUSTES: GASTOS FIJOS (ORDEN DE COLUMNAS PEDIDO)
# ---------------------------------------------------------
elif st.session_state.seccion == 'Ajustes':
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
        if st.button("💾 GUARDAR", use_container_width=True, type="primary"):
            if not df_fijos.empty and cat_sel in df_fijos["Categoría"].values:
                df_fijos.loc[df_fijos["Categoría"] == cat_sel, "Monto_Mensual"] = m_sel
                df_fijos.loc[df_fijos["Categoría"] == cat_sel, "Fondo_Disponible"] = f_sel
            else:
                nuevo = pd.DataFrame([{"Categoría": cat_sel, "Monto_Mensual": m_sel, "Fondo_Disponible": f_sel}])
                df_fijos = pd.concat([df_fijos, nuevo], ignore_index=True)
            conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
            st.cache_data.clear()
            st.rerun()

    st.markdown("---")
    if not df_fijos.empty:
        df_order = df_fijos.copy()
        df_order["Monto Semanal"] = df_order["Monto_Mensual"] / 4
        df_order["Monto Anual"] = df_order["Monto_Mensual"] * 12
        # Orden pedido: Semanal, Mensual, Anual, Fondo
        df_order = df_order[["Categoría", "Monto Semanal", "Monto_Mensual", "Monto Anual", "Fondo_Disponible"]]
        st.dataframe(df_order.style.format("${:,.0f}"), use_container_width=True, height=500, hide_index=True)

# ---------------------------------------------------------
# 3. PAGOS: EXCEPCIONES INDIVIDUALES Y "TODAS"
# ---------------------------------------------------------
elif st.session_state.seccion == 'Pagos':
    st.subheader("💸 Registro de Gastos y Inyección")
    
    # --- BLOQUE INYECCIÓN ---
    col_i1, col_i2, col_i3 = st.columns([2, 1, 1])
    
    with col_i1:
        nombres_cuentas = df_cuentas["Cuenta"].tolist() if not df_cuentas.empty else []
        opciones_inyec = ["TODAS"] + nombres_cuentas
        cuenta_inyec = st.selectbox("📥 Cuenta que recibe el dinero:", opciones_inyec)
        
        # Manejo de excepciones individuales
        if cuenta_inyec != "TODAS":
            exc_c = df_excep[df_excep["Cuenta"] == cuenta_inyec]["Categoria_Excluida"].tolist() if not df_excep.empty else []
            nuevas_exc = st.multiselect(f"Excluir de {cuenta_inyec} para siempre:", df_fijos["Categoría"].tolist(), default=exc_c)
            if st.button("Guardar Excepciones de esta cuenta"):
                # Limpiar viejas y poner nuevas
                if not df_excep.empty: df_excep = df_excep[df_excep["Cuenta"] != cuenta_inyec]
                nuevas_rows = pd.DataFrame([{"Cuenta": cuenta_inyec, "Categoria_Excluida": x} for x in nuevas_exc])
                df_excep = pd.concat([df_excep, nuevas_rows], ignore_index=True)
                conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Excepciones", data=df_excep)
                st.success("Excepciones guardadas.")
        else:
            st.write("Cada cuenta usará sus propias excepciones guardadas.")

    with col_i3:
        st.write("")
        if st.button("➕ AGREGAR OTRA SEMANA", use_container_width=True, type="primary"):
            ctas_a_procesar = nombres_cuentas if cuenta_inyec == "TODAS" else [cuenta_inyec]
            
            for cta in ctas_a_procesar:
                exc_cta = df_excep[df_excep["Cuenta"] == cta]["Categoria_Excluida"].tolist() if not df_excep.empty else []
                # Solo sumar lo que no esté excluido para esta cuenta
                cats_validas = df_fijos[~df_fijos["Categoría"].isin(exc_cta)]
                monto_inyectar = (cats_validas["Monto_Mensual"] / 4).sum()
                
                # Actualizar Sobres (Fondo Disponible)
                for index, row in cats_validas.iterrows():
                    df_fijos.loc[df_fijos["Categoría"] == row["Categoría"], "Fondo_Disponible"] += (row["Monto_Mensual"] / 4)
                
                # Actualizar Banco
                saldo_b = float(df_cuentas.loc[df_cuentas["Cuenta"] == cta, "Saldo"].values[0])
                df_cuentas.loc[df_cuentas["Cuenta"] == cta, "Saldo"] = saldo_b + monto_inyectar
                
                # Movimiento
                nuevo_m = pd.DataFrame([{"Fecha": datetime.now().strftime("%Y-%m-%d"), "Cuenta": cta, "Concepto": "INYECCIÓN SEMANAL", "Monto": monto_inyectar}])
                df_movs = pd.concat([df_movs, nuevo_m], ignore_index=True)

            conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
            conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Cuentas", data=df_cuentas)
            conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Movimientos", data=df_movs)
            st.cache_data.clear()
            st.rerun()

    st.markdown("---")
    # Gasto (Solo resta)
    col_g1, col_g2, col_g3, col_g4 = st.columns(4)
    with col_g1: c_gasto = st.selectbox("Cuenta:", nombres_cuentas)
    with col_g2: s_gasto = st.selectbox("Sobre:", df_fijos["Categoría"].tolist())
    with col_g3: m_gasto = st.number_input("Monto a Restar ($)", min_value=0.0)
    with col_g4:
        st.write("")
        if st.button("RESTAR GASTO", use_container_width=True):
            if m_gasto > 0:
                df_movs = pd.concat([df_movs, pd.DataFrame([{"Fecha": datetime.now().strftime("%Y-%m-%d"), "Cuenta": c_gasto, "Concepto": s_gasto, "Monto": -m_gasto}])], ignore_index=True)
                df_cuentas.loc[df_cuentas["Cuenta"] == c_gasto, "Saldo"] -= m_gasto
                df_fijos.loc[df_fijos["Categoría"] == s_gasto, "Fondo_Disponible"] -= m_gasto
                conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Movimientos", data=df_movs)
                conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Cuentas", data=df_cuentas)
                conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
                st.cache_data.clear()
                st.rerun()

    # Historial Filtrado
    st.markdown("---")
    cf1, cf2 = st.columns([1, 3])
    with cf1:
        f_sel = st.selectbox("Filtrar historial por:", ["TODO"] + df_fijos["Categoría"].tolist())
        st.dataframe(df_fijos[["Categoría", "Fondo_Disponible"]].style.format("${:,.0f}"), use_container_width=True, hide_index=True)
    with cf2:
        df_h = df_movs.sort_index(ascending=False) if f_sel == "TODO" else df_movs[df_movs["Concepto"] == f_sel].sort_index(ascending=False)
        st.dataframe(df_h, use_container_width=True, height=450, hide_index=True)

# ---------------------------------------------------------
# 4. CUENTAS: INTERFAZ BONITA
# ---------------------------------------------------------
elif st.session_state.seccion == 'Cuentas':
    st.subheader("💳 Mis Cuentas Bancarias")
    
    if not df_cuentas.empty:
        df_cuentas["Saldo"] = pd.to_numeric(df_cuentas["Saldo"]).fillna(0)
        t_total = df_cuentas["Saldo"].sum()
        st.markdown(f"<div style='background-color:#e8f5e9; padding:20px; border-radius:10px; text-align:center;'><h2>Balance Total Real: ${t_total:,.2f}</h2></div>", unsafe_allow_html=True)
        
        st.write("")
        # Mostrar como tarjetas
        cols = st.columns(len(df_cuentas))
        for i, (index, row) in enumerate(df_cuentas.iterrows()):
            with cols[i]:
                st.metric(row["Cuenta"], f"${row['Saldo']:,.2f}")

    st.markdown("---")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.write("**Editar o Crear Cuenta**")
        opc = ["➕ NUEVA"] + (df_cuentas["Cuenta"].tolist() if not df_cuentas.empty else [])
        c_edit = st.selectbox("Selecciona cuenta:", opc)
        s_base = float(df_cuentas.loc[df_cuentas["Cuenta"] == c_edit, "Saldo"].values[0]) if c_edit != "➕ NUEVA" else 0.0
        n_nombre = st.text_input("Nombre:") if c_edit == "➕ NUEVA" else c_edit
        n_saldo = st.number_input("Saldo Total Actual:", value=s_base)
        if st.button("GUARDAR CUENTA"):
            if c_edit == "➕ NUEVA":
                df_cuentas = pd.concat([df_cuentas, pd.DataFrame([{"Cuenta": n_nombre, "Saldo": n_saldo}])], ignore_index=True)
            else:
                df_cuentas.loc[df_cuentas["Cuenta"] == c_edit, "Saldo"] = n_saldo
            conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Cuentas", data=df_cuentas)
            st.cache_data.clear()
            st.rerun()
    with col_c2:
        st.write("**Borrar Cuenta**")
        c_del = st.selectbox("Eliminar cuenta:", nombres_cuentas if not df_cuentas.empty else ["Vacío"])
        if st.button("ELIMINAR"):
            df_cuentas = df_cuentas[df_cuentas["Cuenta"] != c_del]
            conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Cuentas", data=df_cuentas)
            st.cache_data.clear()
            st.rerun()