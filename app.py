import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# --- CONFIGURACIÓN DE PANTALLA ---
st.set_page_config(page_title="Gestor Financiero Pro", page_icon="🏦", layout="wide")

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

# Asegurar columnas necesarias
if not df_fijos.empty:
    if "Fondo_Disponible" not in df_fijos.columns: df_fijos["Fondo_Disponible"] = 0.0
    if "Excluir_Inyeccion" not in df_fijos.columns: df_fijos["Excluir_Inyeccion"] = "NO"

# --- NAVEGACIÓN SUPERIOR ---
st.markdown("### 🏦 SISTEMA DE CONTROL FINANCIERO")
col_n1, col_n2, col_n3, col_n4 = st.columns(4)

if 'seccion' not in st.session_state: st.session_state.seccion = 'Vista'

if col_n1.button("📊 PROYECCIÓN ANUAL", use_container_width=True): st.session_state.seccion = 'Vista'
if col_n2.button("⚙️ GASTOS FIJOS", use_container_width=True): st.session_state.seccion = 'Ajustes'
if col_n3.button("💸 REGISTRAR GASTOS", use_container_width=True): st.session_state.seccion = 'Pagos'
if col_n4.button("💳 MIS CUENTAS", use_container_width=True): st.session_state.seccion = 'Cuentas'
st.markdown("---")

# ---------------------------------------------------------
# 1. VISTA: PROYECCIÓN ANUAL (Tabla Ampliada)
# ---------------------------------------------------------
if st.session_state.seccion == 'Vista':
    if not df_fijos.empty:
        st.subheader("📅 Proyección de Gastos Fijos")
        df_anual = pd.DataFrame(index=MESES, columns=df_fijos["Categoría"].tolist())
        for cat in df_fijos["Categoría"]:
            monto = df_fijos.loc[df_fijos["Categoría"] == cat, "Monto_Mensual"].values[0]
            df_anual[cat] = monto
        df_anual.loc["🟢 TOTAL ACUMULADO"] = df_anual.sum()
        st.dataframe(df_anual.style.format("{:,.0f}"), use_container_width=True, height=600)
    else:
        st.write("No hay datos en Gastos Fijos.")

# ---------------------------------------------------------
# 2. AJUSTES: GASTOS FIJOS
# ---------------------------------------------------------
elif st.session_state.seccion == 'Ajustes':
    st.subheader("⚙️ Configurar y Editar Gastos Fijos")
    
    cat_existentes = df_fijos["Categoría"].tolist() if not df_fijos.empty else []
    todas_categorias = sorted(list(set(CATEGORIAS_BASE + cat_existentes)))
    
    c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 1, 1])
    with c1: cat_sel = st.selectbox("Categoría", todas_categorias)
    
    monto_act, fondo_act = 0.0, 0.0
    if not df_fijos.empty and cat_sel in df_fijos["Categoría"].values:
        monto_act = float(df_fijos.loc[df_fijos["Categoría"] == cat_sel, "Monto_Mensual"].values[0])
        fondo_act = float(df_fijos.loc[df_fijos["Categoría"] == cat_sel, "Fondo_Disponible"].values[0])
        
    with c2: monto_sel = st.number_input("Monto Mensual ($)", min_value=0.0, value=monto_act)
    with c3: fondo_sel = st.number_input("Ajustar Fondo ($)", value=fondo_act)
        
    with c4:
        st.write("")
        if st.button("💾 GUARDAR", use_container_width=True, type="primary"):
            if not df_fijos.empty and cat_sel in df_fijos["Categoría"].values:
                df_fijos.loc[df_fijos["Categoría"] == cat_sel, "Monto_Mensual"] = monto_sel
                df_fijos.loc[df_fijos["Categoría"] == cat_sel, "Fondo_Disponible"] = fondo_sel
            else:
                nuevo = pd.DataFrame([{"Categoría": cat_sel, "Monto_Mensual": monto_sel, "Fondo_Disponible": fondo_sel, "Excluir_Inyeccion": "NO"}])
                df_fijos = pd.concat([df_fijos, nuevo], ignore_index=True)
            conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
            st.cache_data.clear()
            st.rerun()
    with c5:
        st.write("")
        if st.button("🗑️ BORRAR", use_container_width=True):
            df_fijos = df_fijos[df_fijos["Categoría"] != cat_sel]
            conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
            st.cache_data.clear()
            st.rerun()

    if not df_fijos.empty:
        df_mostrar = df_fijos[["Categoría", "Monto_Mensual", "Fondo_Disponible", "Excluir_Inyeccion"]]
        st.dataframe(df_mostrar.style.format({"Monto_Mensual": "${:,.0f}", "Fondo_Disponible": "${:,.0f}"}), 
                     use_container_width=True, height=(len(df_fijos)+1)*40, hide_index=True)

# ---------------------------------------------------------
# 3. PAGOS Y MOVIMIENTOS
# ---------------------------------------------------------
elif st.session_state.seccion == 'Pagos':
    st.subheader("💸 Gestión de Fondos y Gastos")
    
    # --- INYECCIÓN SEMANAL ---
    col_e1, col_e2, col_e3 = st.columns([2, 1, 1])
    with col_e1:
        excl_act = df_fijos[df_fijos["Excluir_Inyeccion"] == "SÍ"]["Categoría"].tolist() if not df_fijos.empty else []
        seleccion_excluir = st.multiselect("🚫 EXCLUIR DE LA SEMANA:", df_fijos["Categoría"].tolist() if not df_fijos.empty else [], default=excl_act)
        if st.button("CONFIRMAR EXCEPCIONES"):
            df_fijos["Excluir_Inyeccion"] = df_fijos["Categoría"].apply(lambda x: "SÍ" if x in seleccion_excluir else "NO")
            conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
            st.cache_data.clear()
            st.rerun()

    with col_e2:
        cuenta_ingreso = st.selectbox("📥 Cuenta que recibe el dinero:", df_cuentas["Cuenta"].tolist() if not df_cuentas.empty else ["Crea una cuenta"])

    with col_e3:
        st.write("")
        if st.button("➕ AGREGAR OTRA SEMANA", use_container_width=True, type="primary"):
            if not df_cuentas.empty and not df_fijos.empty:
                df_fijos["Monto_Mensual"] = pd.to_numeric(df_fijos["Monto_Mensual"]).fillna(0)
                df_fijos["Fondo_Disponible"] = pd.to_numeric(df_fijos["Fondo_Disponible"]).fillna(0)
                
                total_inyectar = (df_fijos.loc[df_fijos["Excluir_Inyeccion"] == "NO", "Monto_Mensual"] / 4).sum()
                df_fijos.loc[df_fijos["Excluir_Inyeccion"] == "NO", "Fondo_Disponible"] += (df_fijos["Monto_Mensual"] / 4)
                conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
                
                saldo_banco = float(df_cuentas.loc[df_cuentas["Cuenta"] == cuenta_ingreso, "Saldo"].values[0])
                df_cuentas.loc[df_cuentas["Cuenta"] == cuenta_ingreso, "Saldo"] = saldo_banco + total_inyectar
                conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Cuentas", data=df_cuentas)
                
                fecha_hoy = datetime.now().strftime("%Y-%m-%d")
                mov_ingreso = pd.DataFrame([{"Fecha": fecha_hoy, "Cuenta": cuenta_ingreso, "Concepto": "INYECCIÓN SEMANAL", "Monto": total_inyectar}])
                df_movs = pd.concat([df_movs, mov_ingreso], ignore_index=True)
                conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Movimientos", data=df_movs)

                st.cache_data.clear()
                st.rerun()

    st.markdown("---")
    # --- REGISTRO DE GASTO ---
    st.write("**Registrar Gasto (Se restará solo):**")
    col_g1, col_g2, col_g3, col_g4 = st.columns(4)
    with col_g1: cuenta_gasto = st.selectbox("Cuenta:", df_cuentas["Cuenta"].tolist() if not df_cuentas.empty else [])
    with col_g2: concepto_gasto = st.selectbox("Sobre:", df_fijos["Categoría"].tolist() if not df_fijos.empty else [])
    with col_g3: monto_val = st.number_input("Monto del Gasto ($)", min_value=0.0)
    with col_g4:
        st.write("")
        if st.button("RESTAR GASTO", use_container_width=True):
            if monto_val > 0:
                fecha_hoy = datetime.now().strftime("%Y-%m-%d")
                nuevo_mov = pd.DataFrame([{"Fecha": fecha_hoy, "Cuenta": cuenta_gasto, "Concepto": concepto_gasto, "Monto": -monto_val}])
                df_movs = pd.concat([df_movs, nuevo_mov], ignore_index=True)
                conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Movimientos", data=df_movs)
                
                s_act = float(df_cuentas.loc[df_cuentas["Cuenta"] == cuenta_gasto, "Saldo"].values[0])
                df_cuentas.loc[df_cuentas["Cuenta"] == cuenta_gasto, "Saldo"] = s_act - monto_val
                conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Cuentas", data=df_cuentas)
                
                f_act = float(df_fijos.loc[df_fijos["Categoría"] == concepto_gasto, "Fondo_Disponible"].values[0])
                df_fijos.loc[df_fijos["Categoría"] == concepto_gasto, "Fondo_Disponible"] = f_act - monto_val
                conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
                
                st.cache_data.clear()
                st.rerun()

    st.markdown("---")
    # --- HISTORIAL Y SOBRES ---
    col_f1, col_f2 = st.columns([1, 3])
    with col_f1:
        st.markdown("**💰 Fondos Actuales**")
        df_fijos["Fondo_Disponible"] = pd.to_numeric(df_fijos["Fondo_Disponible"]).fillna(0)
        st.dataframe(df_fijos[["Categoría", "Fondo_Disponible"]].style.format({"Fondo_Disponible": "${:,.0f}"}), 
                     use_container_width=True, height=400, hide_index=True)

    with col_f2:
        lista_filtros = ["VER TODO"] + (df_fijos["Categoría"].tolist() if not df_fijos.empty else [])
        filtro_sel = st.selectbox("📜 Filtrar historial por concepto:", lista_filtros)
        
        if not df_movs.empty:
            if filtro_sel == "VER TODO":
                df_hist_final = df_movs.sort_index(ascending=False)
            else:
                df_hist_final = df_movs[df_movs["Concepto"] == filtro_sel].sort_index(ascending=False)
            
            st.dataframe(df_hist_final, use_container_width=True, height=500, hide_index=True)

# ---------------------------------------------------------
# 4. MIS CUENTAS
# ---------------------------------------------------------
elif st.session_state.seccion == 'Cuentas':
    st.subheader("💳 Gestión de Cuentas")
    col_c1, col_c2 = st.columns([1, 2])
    with col_c1:
        opciones_cta = ["➕ NUEVA CUENTA"] + (df_cuentas["Cuenta"].tolist() if not df_cuentas.empty else [])
        cta_sel = st.selectbox("Cuenta a editar:", opciones_cta)
        
        saldo_act = 0.0
        if cta_sel != "➕ NUEVA CUENTA":
            nombre_cta = cta_sel
            saldo_act = float(df_cuentas.loc[df_cuentas["Cuenta"] == cta_sel, "Saldo"].values[0])
        else:
            nombre_cta = st.text_input("Nombre cuenta nueva")
            
        nuevo_saldo_cta = st.number_input("Saldo Total ($)", value=saldo_act)
        
        if st.button("💾 ACTUALIZAR SALDO TOTAL"):
            if nombre_cta:
                if not df_cuentas.empty and nombre_cta in df_cuentas["Cuenta"].values:
                    df_cuentas.loc[df_cuentas["Cuenta"] == nombre_cta, "Saldo"] = nuevo_saldo_cta
                else:
                    nueva_cta = pd.DataFrame([{"Cuenta": nombre_cta, "Saldo": nuevo_saldo_cta}])
                    df_cuentas = pd.concat([df_cuentas, nueva_cta], ignore_index=True)
                conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Cuentas", data=df_cuentas)
                st.cache_data.clear()
                st.rerun()

    with col_c2:
        if not df_cuentas.empty:
            st.dataframe(df_cuentas.style.format({"Saldo": "${:,.2f}"}), use_container_width=True, hide_index=True)
            st.success(f"**Total Real en Cuentas:** ${df_cuentas['Saldo'].sum():,.2f}")