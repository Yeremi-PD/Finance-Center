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
        return pd.DataFrame()

df_fijos = cargar_hoja("Gastos_Fijos")
df_movs = cargar_hoja("Movimientos")
df_cuentas = cargar_hoja("Cuentas")

# Asegurar que la columna Fondo_Disponible exista en el código
if not df_fijos.empty and "Fondo_Disponible" not in df_fijos.columns:
    df_fijos["Fondo_Disponible"] = 0.0

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
# 2. AJUSTES: GASTOS FIJOS (Con Edición Avanzada)
# ---------------------------------------------------------
elif st.session_state.seccion == 'Ajustes':
    st.subheader("⚙️ Configurar y Editar Gastos Fijos")
    st.info("Selecciona una categoría. Si ya existe, verás sus datos actuales para poder editarlos.")
    
    cat_existentes = df_fijos["Categoría"].tolist() if not df_fijos.empty else []
    todas_categorias = sorted(list(set(CATEGORIAS_BASE + cat_existentes)))
    
    # Hemos añadido una columna más para poder editar el Fondo
    c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 1, 1])
    
    with c1: 
        cat_sel = st.selectbox("Categoría", todas_categorias)
        
    # Lógica para "Cargar" los datos actuales si la categoría ya existe
    monto_actual = 0.0
    fondo_actual = 0.0
    if not df_fijos.empty and cat_sel in df_fijos["Categoría"].values:
        monto_actual = float(df_fijos.loc[df_fijos["Categoría"] == cat_sel, "Monto_Mensual"].values[0])
        fondo_actual = float(df_fijos.loc[df_fijos["Categoría"] == cat_sel, "Fondo_Disponible"].values[0])
        
    with c2: 
        # Mostramos el monto actual por defecto
        monto_sel = st.number_input("Monto Mensual ($)", min_value=0.0, step=100.0, value=monto_actual)
    with c3:
        # Permitimos editar el fondo acumulado manualmente (por si hay algún error o quieres ajustarlo)
        fondo_sel = st.number_input("Ajustar Fondo ($)", value=fondo_actual, step=10.0)
        
    with c4:
        st.write("")
        if st.button("💾 GUARDAR", use_container_width=True, type="primary"):
            if not df_fijos.empty and cat_sel in df_fijos["Categoría"].values:
                # Actualizar categoría existente
                df_fijos.loc[df_fijos["Categoría"] == cat_sel, "Monto_Mensual"] = monto_sel
                df_fijos.loc[df_fijos["Categoría"] == cat_sel, "Fondo_Disponible"] = fondo_sel
            else:
                # Crear nueva categoría
                nuevo = pd.DataFrame([{"Categoría": cat_sel, "Monto_Mensual": monto_sel, "Fondo_Disponible": fondo_sel}])
                df_fijos = pd.concat([df_fijos, nuevo], ignore_index=True)
            
            conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
            st.cache_data.clear()
            st.success("¡Datos actualizados!")
            st.rerun()
            
    with c5:
        st.write("")
        if st.button("🗑️ BORRAR", use_container_width=True):
            if not df_fijos.empty and cat_sel in df_fijos["Categoría"].values:
                df_fijos = df_fijos[df_fijos["Categoría"] != cat_sel]
                conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
                st.cache_data.clear()
                st.rerun()
            else:
                st.warning("Esa categoría no existe aún.")

    # Mostrar tabla con el Fondo Disponible
    st.markdown("**Presupuesto y Fondos Actuales:**")
    if not df_fijos.empty:
        df_mostrar = df_fijos.copy()
        df_mostrar["Gasto Semanal"] = pd.to_numeric(df_mostrar["Monto_Mensual"], errors="coerce") / 4
        # Formatear como dinero
        df_mostrar = df_mostrar[["Categoría", "Monto_Mensual", "Gasto Semanal", "Fondo_Disponible"]]
        st.dataframe(df_mostrar.style.format({"Monto_Mensual": "${:,.2f}", "Gasto Semanal": "${:,.2f}", "Fondo_Disponible": "${:,.2f}"}), use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# 3. PAGOS Y MOVIMIENTOS (Botón Semanal + Filtro por Categoría)
# ---------------------------------------------------------
elif st.session_state.seccion == 'Pagos':
    st.subheader("💸 Control de Pagos y Sobres")
    
    # --- BOTÓN MÁGICO DE INYECCIÓN SEMANAL ---
    st.markdown("### 📥 Ingreso Semanal Automático")
    st.info("Al presionar este botón, se sumará a cada Categoría su presupuesto de 1 semana (Monto Mensual / 4).")
    if st.button("➕ AGREGAR FONDOS DE OTRA SEMANA", use_container_width=True):
        if not df_fijos.empty:
            df_fijos["Monto_Mensual"] = pd.to_numeric(df_fijos["Monto_Mensual"], errors="coerce").fillna(0)
            df_fijos["Fondo_Disponible"] = pd.to_numeric(df_fijos["Fondo_Disponible"], errors="coerce").fillna(0)
            
            # Sumar una semana (mes / 4) al fondo de cada categoría
            df_fijos["Fondo_Disponible"] += (df_fijos["Monto_Mensual"] / 4)
            
            conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
            st.cache_data.clear()
            st.success("¡Fondos inyectados correctamente a todas tus categorías! 🎉")
            st.rerun()
        else:
            st.error("No hay gastos fijos configurados.")

    st.markdown("---")
    st.markdown("### 📤 Registrar Nuevo Gasto/Ingreso")
    
    if df_cuentas.empty or "Cuenta" not in df_cuentas.columns:
        st.error("⚠️ Crea una Cuenta en la pestaña 'MIS CUENTAS' primero.")
    else:
        conceptos_existentes = df_fijos["Categoría"].tolist() if not df_fijos.empty else CATEGORIAS_BASE
        opciones_concepto = ["➕ OTRO (Escribir nuevo)"] + conceptos_existentes
        
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1: cuenta_sel = st.selectbox("¿De qué cuenta sale?", df_cuentas["Cuenta"].tolist())
        with col_m2:
            concepto_sel = st.selectbox("Concepto (Sobre)", opciones_concepto)
            concepto_final = st.text_input("Escribe el nuevo concepto:") if concepto_sel == "➕ OTRO (Escribir nuevo)" else concepto_sel
        with col_m3: monto_mov = st.number_input("Monto ($)", format="%.2f", help="Negativo para restar (-500)")
        with col_m4:
            st.write("")
            if st.button("REGISTRAR", use_container_width=True, type="primary"):
                if concepto_sel == "➕ OTRO (Escribir nuevo)" and not concepto_final:
                    st.error("Escribe un concepto.")
                else:
                    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
                    
                    # 1. Registrar Movimiento
                    nuevo_mov = pd.DataFrame([{"Fecha": fecha_hoy, "Cuenta": cuenta_sel, "Concepto": concepto_final, "Monto": monto_mov}])
                    df_movs_up = pd.concat([df_movs, nuevo_mov], ignore_index=True)
                    conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Movimientos", data=df_movs_up)
                    
                    # 2. Descontar de la Cuenta de Banco
                    saldo_actual = pd.to_numeric(df_cuentas.loc[df_cuentas["Cuenta"] == cuenta_sel, "Saldo"].values[0])
                    df_cuentas.loc[df_cuentas["Cuenta"] == cuenta_sel, "Saldo"] = saldo_actual + monto_mov
                    conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Cuentas", data=df_cuentas)

                    # 3. Descontar del "Fondo Disponible" del Concepto (Si existe)
                    if not df_fijos.empty and concepto_final in df_fijos["Categoría"].values:
                        fondo_actual = pd.to_numeric(df_fijos.loc[df_fijos["Categoría"] == concepto_final, "Fondo_Disponible"].values[0])
                        df_fijos.loc[df_fijos["Categoría"] == concepto_final, "Fondo_Disponible"] = fondo_actual + monto_mov
                        conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)

                    st.cache_data.clear()
                    st.success("Movimiento registrado exitosamente.")
                    st.rerun()

        st.markdown("---")
        # --- TABLAS INDIVIDUALES POR CONCEPTO ---
        st.markdown("### 🔍 Análisis por Concepto")
        st.info("Elige una categoría para ver cuánto dinero tiene acumulado y todos sus movimientos.")
        concepto_ver = st.selectbox("Selecciona una Categoría para revisar:", conceptos_existentes)
        
        col_v1, col_v2 = st.columns([1, 2])
        with col_v1:
            if not df_fijos.empty and concepto_ver in df_fijos["Categoría"].values:
                fondo = pd.to_numeric(df_fijos.loc[df_fijos["Categoría"] == concepto_ver, "Fondo_Disponible"].values[0])
                # Mostrar en verde si hay dinero, en rojo si te pasaste
                color = "normal" if fondo >= 0 else "inverse"
                st.metric(label=f"Fondo de '{concepto_ver}'", value=f"${fondo:,.2f}", delta=None)
        
        with col_v2:
            if not df_movs.empty:
                movs_filtrados = df_movs[df_movs["Concepto"] == concepto_ver]
                if not movs_filtrados.empty:
                    st.dataframe(movs_filtrados.sort_index(ascending=False), use_container_width=True, hide_index=True)
                else:
                    st.write(f"No hay movimientos registrados para {concepto_ver}.")

# ---------------------------------------------------------
# 4. MIS CUENTAS
# ---------------------------------------------------------
elif st.session_state.seccion == 'Cuentas':
    st.subheader("💳 Gestión de Cuentas")
    col_c1, col_c2 = st.columns([1, 2])
    with col_c1:
        nombre_cta = st.text_input("Nombre de la Cuenta")
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
        
        st.markdown("---")
        cuenta_eliminar = st.selectbox("Selecciona la cuenta a borrar", df_cuentas["Cuenta"].tolist() if not df_cuentas.empty else ["No hay cuentas"])
        if st.button("🗑️ Eliminar Cuenta", use_container_width=True):
            if not df_cuentas.empty and cuenta_eliminar != "No hay cuentas":
                df_cuentas = df_cuentas[df_cuentas["Cuenta"] != cuenta_eliminar]
                conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Cuentas", data=df_cuentas)
                st.cache_data.clear()
                st.rerun()

    with col_c2:
        if not df_cuentas.empty:
            df_cuentas['Saldo'] = pd.to_numeric(df_cuentas['Saldo'], errors='coerce').fillna(0)
            st.dataframe(df_cuentas.style.format({"Saldo": "${:,.2f}"}), use_container_width=True, hide_index=True)
            st.success(f"**Total Disponible (Dinero Real):** ${df_cuentas['Saldo'].sum():,.2f}")