import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Mi Banco Personal", page_icon="🏦", layout="wide")
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

if not df_fijos.empty and "Fondo_Disponible" not in df_fijos.columns:
    df_fijos["Fondo_Disponible"] = 0.0

# --- NAVEGACIÓN ---
st.markdown("### 🏦 SISTEMA FINANCIERO INTEGRAL")
col_n1, col_n2, col_n3, col_n4 = st.columns(4)

if 'seccion' not in st.session_state: st.session_state.seccion = 'Vista'

if col_n1.button("📊 PROYECCIÓN ANUAL", use_container_width=True): st.session_state.seccion = 'Vista'
if col_n2.button("⚙️ GASTOS FIJOS", use_container_width=True): st.session_state.seccion = 'Ajustes'
if col_n3.button("💸 REGISTRAR GASTOS", use_container_width=True): st.session_state.seccion = 'Pagos'
if col_n4.button("💳 MIS CUENTAS", use_container_width=True): st.session_state.seccion = 'Cuentas'
st.markdown("---")

# ---------------------------------------------------------
# 1. VISTA: PROYECCIÓN ANUAL (Sin Scroll)
# ---------------------------------------------------------
if st.session_state.seccion == 'Vista':
    if not df_fijos.empty and "Categoría" in df_fijos.columns:
        st.subheader("📅 Proyección de Gastos Fijos")
        df_anual = pd.DataFrame(index=MESES, columns=df_fijos["Categoría"].tolist())
        for cat in df_fijos["Categoría"]:
            monto = df_fijos.loc[df_fijos["Categoría"] == cat, "Monto_Mensual"].values[0]
            df_anual[cat] = monto
        df_anual.loc["🟢 TOTAL ACUMULADO"] = df_anual.sum()
        
        # Altura dinámica: 13 filas (12 meses + total) * 38px + 40px de encabezado = ~550px
        st.dataframe(df_anual.style.format("{:,.2f}"), use_container_width=True, height=550)
    else:
        st.warning("No hay gastos fijos registrados.")

# ---------------------------------------------------------
# 2. AJUSTES: GASTOS FIJOS (Edición directa y sin scroll)
# ---------------------------------------------------------
elif st.session_state.seccion == 'Ajustes':
    st.subheader("⚙️ Configurar y Editar Gastos Fijos")
    
    cat_existentes = df_fijos["Categoría"].tolist() if not df_fijos.empty else []
    todas_categorias = sorted(list(set(CATEGORIAS_BASE + cat_existentes)))
    
    c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 1, 1])
    with c1: cat_sel = st.selectbox("Categoría", todas_categorias)
    
    monto_actual, fondo_actual = 0.0, 0.0
    if not df_fijos.empty and cat_sel in df_fijos["Categoría"].values:
        monto_actual = float(df_fijos.loc[df_fijos["Categoría"] == cat_sel, "Monto_Mensual"].values[0])
        fondo_actual = float(df_fijos.loc[df_fijos["Categoría"] == cat_sel, "Fondo_Disponible"].values[0])
        
    with c2: monto_sel = st.number_input("Monto Mensual ($)", min_value=0.0, step=100.0, value=monto_actual)
    with c3: fondo_sel = st.number_input("Ajustar Fondo ($)", value=fondo_actual, step=10.0)
        
    with c4:
        st.write("")
        if st.button("💾 GUARDAR", use_container_width=True, type="primary"):
            if not df_fijos.empty and cat_sel in df_fijos["Categoría"].values:
                df_fijos.loc[df_fijos["Categoría"] == cat_sel, "Monto_Mensual"] = monto_sel
                df_fijos.loc[df_fijos["Categoría"] == cat_sel, "Fondo_Disponible"] = fondo_sel
            else:
                nuevo = pd.DataFrame([{"Categoría": cat_sel, "Monto_Mensual": monto_sel, "Fondo_Disponible": fondo_sel}])
                df_fijos = pd.concat([df_fijos, nuevo], ignore_index=True)
            conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
            st.cache_data.clear()
            st.rerun()
            
    with c5:
        st.write("")
        if st.button("🗑️ BORRAR", use_container_width=True):
            if not df_fijos.empty and cat_sel in df_fijos["Categoría"].values:
                df_fijos = df_fijos[df_fijos["Categoría"] != cat_sel]
                conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
                st.cache_data.clear()
                st.rerun()

    st.markdown("**Presupuesto y Fondos Actuales:**")
    if not df_fijos.empty:
        df_mostrar = df_fijos.copy()
        df_mostrar["Gasto Semanal"] = pd.to_numeric(df_mostrar["Monto_Mensual"], errors="coerce") / 4
        df_mostrar = df_mostrar[["Categoría", "Monto_Mensual", "Gasto Semanal", "Fondo_Disponible"]]
        
        # Tamaño depende de los elementos para no hacer scroll
        altura_dinamica = (len(df_mostrar) + 1) * 38 + 20
        st.dataframe(df_mostrar.style.format({"Monto_Mensual": "${:,.2f}", "Gasto Semanal": "${:,.2f}", "Fondo_Disponible": "${:,.2f}"}), 
                     use_container_width=True, height=altura_dinamica, hide_index=True)

# ---------------------------------------------------------
# 3. PAGOS (Solo resta dinero y tableros separados)
# ---------------------------------------------------------
elif st.session_state.seccion == 'Pagos':
    st.subheader("💸 Registro de Gastos")
    
    # ÚNICA FORMA DE SUMAR DINERO
    st.info("💡 La única forma de aumentar los fondos es inyectando el dinero de tu semana/quincena.")
    if st.button("➕ INYECTAR FONDOS SEMANALES A LOS SOBRES", use_container_width=True):
        if not df_fijos.empty:
            df_fijos["Monto_Mensual"] = pd.to_numeric(df_fijos["Monto_Mensual"], errors="coerce").fillna(0)
            df_fijos["Fondo_Disponible"] = pd.to_numeric(df_fijos["Fondo_Disponible"], errors="coerce").fillna(0)
            df_fijos["Fondo_Disponible"] += (df_fijos["Monto_Mensual"] / 4)
            conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
            st.cache_data.clear()
            st.success("¡Fondos inyectados! El dinero ya está en los sobres.")
            st.rerun()

    st.markdown("---")
    st.markdown("### 📤 Registrar Nuevo Gasto")
    st.warning("Escribe el monto normalmente (ej: 500). El sistema se encargará de RESTARLO automáticamente.")
    
    if df_cuentas.empty or df_fijos.empty:
        st.error("⚠️ Asegúrate de tener al menos una Cuenta y un Gasto Fijo creados para poder registrar compras.")
    else:
        col_g1, col_g2, col_g3, col_g4 = st.columns(4)
        with col_g1: cuenta_sel = st.selectbox("Se pagó con la cuenta:", df_cuentas["Cuenta"].tolist())
        with col_g2: concepto_sel = st.selectbox("Se gastó del sobre:", df_fijos["Categoría"].tolist())
        with col_g3: monto_gasto = st.number_input("Monto Gastado ($)", min_value=0.0, step=50.0)
        with col_g4:
            st.write("")
            if st.button("RESTAR GASTO", use_container_width=True, type="primary"):
                if monto_gasto > 0:
                    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
                    # 1. Guardar movimiento en negativo (como es un gasto)
                    nuevo_mov = pd.DataFrame([{"Fecha": fecha_hoy, "Cuenta": cuenta_sel, "Concepto": concepto_sel, "Monto": -monto_gasto}])
                    df_movs = pd.concat([df_movs, nuevo_mov], ignore_index=True)
                    conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Movimientos", data=df_movs)
                    
                    # 2. Descontar de la Cuenta Real
                    saldo_cta = float(df_cuentas.loc[df_cuentas["Cuenta"] == cuenta_sel, "Saldo"].values[0])
                    df_cuentas.loc[df_cuentas["Cuenta"] == cuenta_sel, "Saldo"] = saldo_cta - monto_gasto
                    conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Cuentas", data=df_cuentas)

                    # 3. Descontar del Sobre Virtual
                    fondo_actual = float(df_fijos.loc[df_fijos["Categoría"] == concepto_sel, "Fondo_Disponible"].values[0])
                    df_fijos.loc[df_fijos["Categoría"] == concepto_sel, "Fondo_Disponible"] = fondo_actual - monto_gasto
                    conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)

                    st.cache_data.clear()
                    st.success("Gasto registrado y descontado correctamente.")
                    st.rerun()
                else:
                    st.error("Pon un monto mayor a cero.")

        # TABLAS INFERIORES
        st.markdown("---")
        st.markdown("### 📊 Estado de tus Sobres y Movimientos")
        col_t1, col_t2 = st.columns(2)
        
        with col_t1:
            st.markdown("**💰 Dinero en cada Sobre**")
            df_sobres = df_fijos[["Categoría", "Fondo_Disponible"]].copy()
            altura_sobres = (len(df_sobres) + 1) * 38 + 20
            st.dataframe(df_sobres.style.format({"Fondo_Disponible": "${:,.2f}"}), use_container_width=True, height=altura_sobres, hide_index=True)
            
        with col_t2:
            st.markdown("**📉 Últimos Gastos Registrados**")
            if not df_movs.empty:
                altura_movs = min(600, (len(df_movs) + 1) * 38 + 20)
                st.dataframe(df_movs.sort_index(ascending=False), use_container_width=True, height=altura_movs, hide_index=True)
            else:
                st.info("Aún no tienes movimientos registrados.")

# ---------------------------------------------------------
# 4. MIS CUENTAS (Editor directo de Saldos)
# ---------------------------------------------------------
elif st.session_state.seccion == 'Cuentas':
    st.subheader("💳 Gestión y Edición de Cuentas")
    
    col_c1, col_c2 = st.columns([1, 2])
    with col_c1:
        st.markdown("**Editar Saldo o Crear Cuenta**")
        nombres_ctas = df_cuentas["Cuenta"].tolist() if not df_cuentas.empty else []
        opciones_cta = ["➕ CREAR NUEVA CUENTA"] + nombres_ctas
        
        cta_sel = st.selectbox("Selecciona la cuenta (o elige Crear Nueva)", opciones_cta)
        
        saldo_actual = 0.0
        if cta_sel == "➕ CREAR NUEVA CUENTA":
            nombre_cta = st.text_input("Nombre de la nueva cuenta")
        else:
            nombre_cta = cta_sel
            saldo_actual = float(df_cuentas.loc[df_cuentas["Cuenta"] == cta_sel, "Saldo"].values[0])
            
        saldo_cta = st.number_input("Saldo Total de la Cuenta ($)", value=saldo_actual, step=50.0)
        
        if st.button("💾 GUARDAR SALDO", type="primary", use_container_width=True):
            if nombre_cta:
                if not df_cuentas.empty and nombre_cta in df_cuentas["Cuenta"].values:
                    df_cuentas.loc[df_cuentas["Cuenta"] == nombre_cta, "Saldo"] = saldo_cta
                else:
                    nueva_cta = pd.DataFrame([{"Cuenta": nombre_cta, "Saldo": saldo_cta}])
                    df_cuentas = pd.concat([df_cuentas, nueva_cta], ignore_index=True)
                conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Cuentas", data=df_cuentas)
                st.cache_data.clear()
                st.rerun()
            else:
                st.warning("Falta el nombre.")

    with col_c2:
        st.markdown("**Tus Cuentas Reales**")
        if not df_cuentas.empty:
            df_cuentas['Saldo'] = pd.to_numeric(df_cuentas['Saldo'], errors='coerce').fillna(0)
            st.dataframe(df_cuentas.style.format({"Saldo": "${:,.2f}"}), use_container_width=True, hide_index=True)
            st.success(f"**Suma de todo tu dinero:** ${df_cuentas['Saldo'].sum():,.2f}")