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
        df = conn.read(spreadsheet=URL_GOOGLE_SHEET, worksheet=nombre).dropna(how="all")
        return df
    except:
        return pd.DataFrame() # Si hay error, devuelve tabla vacía

df_fijos = cargar_hoja("Gastos_Fijos")
df_movs = cargar_hoja("Movimientos")
df_cuentas = cargar_hoja("Cuentas")

# --- NAVEGACIÓN ---
st.markdown("### 🏦 SISTEMA FINANCIERO INTEGRAL")
col_n1, col_n2, col_n3, col_n4 = st.columns(4)

if 'seccion' not in st.session_state: st.session_state.seccion = 'Vista'

if col_n1.button("📊 PROYECCIÓN ANUAL", use_container_width=True): st.session_state.seccion = 'Vista'
if col_n2.button("⚙️ GASTOS FIJOS", use_container_width=True): st.session_state.seccion = 'Ajustes'
if col_n3.button("💸 PAGOS Y MOVIMIENTOS", use_container_width=True): st.session_state.seccion = 'Pagos'
if col_n4.button("💳 MIS CUENTAS", use_container_width=True): st.session_state.seccion = 'Cuentas'
st.markdown("---")

# ---------------------------------------------------------
# 1. VISTA: PROYECCIÓN ANUAL
# ---------------------------------------------------------
if st.session_state.seccion == 'Vista':
    if not df_fijos.empty and "Categoría" in df_fijos.columns:
        st.subheader("📅 Proyección de Gastos Fijos")
        df_anual = pd.DataFrame(index=MESES, columns=df_fijos["Categoría"].tolist())
        for cat in df_fijos["Categoría"]:
            monto = df_fijos.loc[df_fijos["Categoría"] == cat, "Monto_Mensual"].values[0]
            df_anual[cat] = monto
        df_anual.loc["🟢 TOTAL ACUMULADO"] = df_anual.sum()
        st.dataframe(df_anual.style.format("{:,.2f}"), use_container_width=True)
    else:
        st.warning("No hay gastos fijos registrados. Ve a la pestaña 'GASTOS FIJOS'.")

# ---------------------------------------------------------
# 2. AJUSTES: GASTOS FIJOS (Agregar, Modificar, Eliminar)
# ---------------------------------------------------------
elif st.session_state.seccion == 'Ajustes':
    st.subheader("⚙️ Configurar Gastos Fijos")
    st.info("Si seleccionas una categoría que ya existe y le cambias el monto, se actualizará. También puedes eliminarla.")
    
    # Combinar categorías base con las que ya existan en la tabla
    cat_existentes = df_fijos["Categoría"].tolist() if not df_fijos.empty else []
    todas_categorias = sorted(list(set(CATEGORIAS_BASE + cat_existentes)))
    
    c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
    with c1: cat_sel = st.selectbox("Categoría", todas_categorias)
    with c2: monto_sel = st.number_input("Monto Mensual ($)", min_value=0.0, step=100.0)
    with c3:
        st.write("")
        if st.button("💾 GUARDAR", use_container_width=True, type="primary"):
            if not df_fijos.empty and cat_sel in df_fijos["Categoría"].values:
                df_fijos.loc[df_fijos["Categoría"] == cat_sel, "Monto_Mensual"] = monto_sel
            else:
                nuevo = pd.DataFrame([{"Categoría": cat_sel, "Monto_Mensual": monto_sel}])
                df_fijos = pd.concat([df_fijos, nuevo], ignore_index=True)
            conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
            st.cache_data.clear()
            st.rerun()
    with c4:
        st.write("")
        if st.button("🗑️ ELIMINAR", use_container_width=True):
            if not df_fijos.empty and cat_sel in df_fijos["Categoría"].values:
                df_fijos = df_fijos[df_fijos["Categoría"] != cat_sel]
                conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
                st.cache_data.clear()
                st.rerun()
            else:
                st.warning("Esa categoría no está en la tabla.")
    
    st.markdown("**Presupuesto Actual Guardado:**")
    st.dataframe(df_fijos, use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# 3. PAGOS Y MOVIMIENTOS (Conceptos mixtos y descuento a cuenta)
# ---------------------------------------------------------
elif st.session_state.seccion == 'Pagos':
    st.subheader("💸 Registrar Pago o Ingreso")
    
    if df_cuentas.empty or "Cuenta" not in df_cuentas.columns:
        st.error("⚠️ Primero debes crear una Cuenta en la pestaña 'MIS CUENTAS' para poder hacer movimientos.")
    else:
        # Calcular saldo total de todas las cuentas
        df_cuentas['Saldo'] = pd.to_numeric(df_cuentas['Saldo'], errors='coerce').fillna(0)
        st.metric("💰 BALANCE TOTAL EN CUENTAS", f"${df_cuentas['Saldo'].sum():,.2f}")
        st.markdown("---")
        
        # Opciones de Concepto
        conceptos_existentes = df_fijos["Categoría"].tolist() if not df_fijos.empty else CATEGORIAS_BASE
        opciones_concepto = ["➕ OTRO (Escribir nuevo)"] + conceptos_existentes
        
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        
        with col_m1:
            cuenta_sel = st.selectbox("¿De qué cuenta sale/entra?", df_cuentas["Cuenta"].tolist())
        with col_m2:
            concepto_sel = st.selectbox("Concepto", opciones_concepto)
            if concepto_sel == "➕ OTRO (Escribir nuevo)":
                concepto_final = st.text_input("Escribe el nuevo concepto:")
            else:
                concepto_final = concepto_sel
        with col_m3:
            monto_mov = st.number_input("Monto ($)", format="%.2f", help="Negativo para restar (-500), Positivo para sumar (500)")
        with col_m4:
            st.write("")
            if st.button("REGISTRAR", use_container_width=True, type="primary"):
                if concepto_sel == "➕ OTRO (Escribir nuevo)" and not concepto_final:
                    st.error("Escribe un concepto.")
                else:
                    # 1. Guardar el movimiento
                    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
                    nuevo_mov = pd.DataFrame([{"Fecha": fecha_hoy, "Cuenta": cuenta_sel, "Concepto": concepto_final, "Monto": monto_mov}])
                    df_movs_up = pd.concat([df_movs, nuevo_mov], ignore_index=True)
                    conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Movimientos", data=df_movs_up)
                    
                    # 2. Actualizar el saldo de la cuenta elegida
                    saldo_actual = df_cuentas.loc[df_cuentas["Cuenta"] == cuenta_sel, "Saldo"].values[0]
                    nuevo_saldo = float(saldo_actual) + float(monto_mov)
                    df_cuentas.loc[df_cuentas["Cuenta"] == cuenta_sel, "Saldo"] = nuevo_saldo
                    conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Cuentas", data=df_cuentas)
                    
                    st.cache_data.clear()
                    st.success(f"Movimiento registrado. Nuevo saldo en {cuenta_sel}: ${nuevo_saldo:,.2f}")
                    st.rerun()

        st.markdown("### Historial de Movimientos")
        st.dataframe(df_movs.sort_index(ascending=False), use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# 4. MIS CUENTAS (Agregar, Modificar, Eliminar Cuentas)
# ---------------------------------------------------------
elif st.session_state.seccion == 'Cuentas':
    st.subheader("💳 Gestión de Cuentas")
    
    col_c1, col_c2 = st.columns([1, 2])
    
    with col_c1:
        st.markdown("**Agregar o Modificar Cuenta**")
        st.info("Si pones el nombre de una cuenta que ya existe, se actualizará su saldo. Si no, se creará una nueva.")
        nombre_cta = st.text_input("Nombre de la Cuenta (ej: Banreservas, Efectivo)")
        saldo_cta = st.number_input("Saldo Actual ($)", format="%.2f")
        
        if st.button("💾 Guardar Cuenta", type="primary", use_container_width=True):
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
                st.warning("Escribe un nombre de cuenta.")
        
        st.markdown("---")
        st.markdown("**Eliminar Cuenta**")
        cuenta_eliminar = st.selectbox("Selecciona la cuenta a borrar", df_cuentas["Cuenta"].tolist() if not df_cuentas.empty else ["No hay cuentas"])
        if st.button("🗑️ Eliminar Cuenta", use_container_width=True):
            if not df_cuentas.empty and cuenta_eliminar != "No hay cuentas":
                df_cuentas = df_cuentas[df_cuentas["Cuenta"] != cuenta_eliminar]
                conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Cuentas", data=df_cuentas)
                st.cache_data.clear()
                st.rerun()

    with col_c2:
        st.markdown("**Lista de Cuentas Activas**")
        if not df_cuentas.empty:
            df_cuentas['Saldo'] = pd.to_numeric(df_cuentas['Saldo'], errors='coerce').fillna(0)
            # Mostrar la tabla bonita con el símbolo de dólar
            st.dataframe(df_cuentas.style.format({"Saldo": "${:,.2f}"}), use_container_width=True, hide_index=True)
            st.success(f"**Gran Total Disponible:** ${df_cuentas['Saldo'].sum():,.2f}")
        else:
            st.info("Aún no tienes cuentas registradas.")