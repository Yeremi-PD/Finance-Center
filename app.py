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

# --- CARGAR DATOS (MEMORIA LOCAL) ---
def cargar_base_datos(nombre):
    # Aquí sí usamos un ttl mayor (ej. 3600 segundos) para que no descargue en cada clic
    try:
        df = conn.read(spreadsheet=URL_GOOGLE_SHEET, worksheet=nombre, ttl=3600).dropna(how="all")
        if df.empty:
            columnas = {
                "Gastos_Fijos": ["Categoría", "Monto_Mensual", "Fondo_Disponible"],
                "Movimientos": ["Fecha", "Cuenta", "Concepto", "Monto"],
                "Cuentas": ["Cuenta", "Saldo"],
                "Excepciones": ["Cuenta", "Categoria_Excluida"],
                "Trading": ["Fecha", "Cuenta", "Tipo", "Concepto", "Monto"]
            }
            return pd.DataFrame(columns=columnas.get(nombre, []))
        if nombre == "Gastos_Fijos" and "Fondo_Disponible" not in df.columns:
            df["Fondo_Disponible"] = 0.0
        return df
    except:
        return pd.DataFrame()

# Solo descargamos de Google Sheets si la app se acaba de abrir o se refrescó con F5
if 'df_fijos' not in st.session_state:
    st.session_state.df_fijos = cargar_base_datos("Gastos_Fijos")
    st.session_state.df_movs = cargar_base_datos("Movimientos")
    st.session_state.df_cuentas = cargar_base_datos("Cuentas")
    st.session_state.df_excep = cargar_base_datos("Excepciones")
    st.session_state.df_trading = cargar_base_datos("Trading")

# Usamos las variables de la sesión para que todo sea instantáneo
df_fijos = st.session_state.df_fijos
df_movs = st.session_state.df_movs
df_cuentas = st.session_state.df_cuentas
df_excep = st.session_state.df_excep
df_trading = st.session_state.df_trading # Nueva hoja cargada


# --- NAVEGACIÓN ---
st.markdown("<h1 style='text-align: center; color: #4CAF50;'>💰 MY FINANCIAL CENTER</h1>", unsafe_allow_html=True)
col_n1, col_n2, col_n3, col_n4, col_n5 = st.columns(5)

# Por defecto, abrimos la primera pestaña del nuevo orden
if 'seccion' not in st.session_state: st.session_state.seccion = 'Ajustes'

with col_n1:
    if st.button("⚙️ GASTOS FIJOS", use_container_width=True, type="primary" if st.session_state.seccion == 'Ajustes' else "secondary"): 
        st.session_state.seccion = 'Ajustes'
        st.rerun()
with col_n2:
    if st.button("💸 REGISTRAR GASTOS", use_container_width=True, type="primary" if st.session_state.seccion == 'Pagos' else "secondary"): 
        st.session_state.seccion = 'Pagos'
        st.rerun()
with col_n3:
    if st.button("📈 TRADING", use_container_width=True, type="primary" if st.session_state.seccion == 'Trading' else "secondary"): 
        st.session_state.seccion = 'Trading'
        st.rerun()
with col_n4:
    if st.button("📊 PROYECCIÓN ANUAL", use_container_width=True, type="primary" if st.session_state.seccion == 'Vista' else "secondary"): 
        st.session_state.seccion = 'Vista'
        st.rerun()
with col_n5:
    if st.button("💳 MIS CUENTAS", use_container_width=True, type="primary" if st.session_state.seccion == 'Cuentas' else "secondary"): 
        st.session_state.seccion = 'Cuentas'
        st.rerun()
st.markdown("---")

# ---------------------------------------------------------
# 1. VISTA: PROYECCIÓN ANUAL 
# ---------------------------------------------------------
if st.session_state.seccion == 'Vista':
    if not df_fijos.empty:
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
        
        # Tabla sin fondo blanco, se adapta perfectamente a tu tema
        st.dataframe(df_anual.style.format("{:,.0f}"), use_container_width=True, height=550)

# ---------------------------------------------------------
# 2. AJUSTES: GASTOS FIJOS 
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
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("💾", help="Guardar/Actualizar", use_container_width=True, type="primary"):
                if not df_fijos.empty and cat_sel in df_fijos["Categoría"].values:
                    df_fijos.loc[df_fijos["Categoría"] == cat_sel, "Monto_Mensual"] = m_sel
                    df_fijos.loc[df_fijos["Categoría"] == cat_sel, "Fondo_Disponible"] = f_sel
                else:
                    nuevo = pd.DataFrame([{"Categoría": cat_sel, "Monto_Mensual": m_sel, "Fondo_Disponible": f_sel}])
                    df_fijos = pd.concat([df_fijos, nuevo], ignore_index=True)
                conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
                # ACTUALIZAR MEMORIA LOCAL PARA QUE EL BALANCE CAMBIE AL INSTANTE
                st.session_state.df_fijos = df_fijos 
                st.rerun()
        with col_btn2:
            if st.button("🗑️", help="Eliminar Categoría", use_container_width=True):
                if not df_fijos.empty and cat_sel in df_fijos["Categoría"].values:
                    df_fijos = df_fijos[df_fijos["Categoría"] != cat_sel]
                    conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
                    st.cache_data.clear()
                    st.rerun()

    st.markdown("---")
    if not df_fijos.empty:
        df_order = df_fijos.copy()
        df_order["Monto Semanal"] = pd.to_numeric(df_order["Monto_Mensual"]) / 4
        df_order["Monto Anual"] = pd.to_numeric(df_order["Monto_Mensual"]) * 12
        df_order["Fondo_Disponible"] = pd.to_numeric(df_order["Fondo_Disponible"])
        
        # Orden pedido: Semanal, Mensual, Anual, Fondo
        df_order = df_order[["Categoría", "Monto Semanal", "Monto_Mensual", "Monto Anual", "Fondo_Disponible"]]
        
        # ERROR CORREGIDO AQUÍ:
        st.dataframe(df_order.style.format({
            "Monto Semanal": "${:,.0f}", 
            "Monto_Mensual": "${:,.0f}", 
            "Monto Anual": "${:,.0f}", 
            "Fondo_Disponible": "${:,.0f}"
        }), use_container_width=True, height=500, hide_index=True)

# ---------------------------------------------------------
# 3. PAGOS Y EXCEPCIONES (Interfaz Premium y Limpia)
# ---------------------------------------------------------
elif st.session_state.seccion == 'Pagos':
    st.markdown("<h2 style='color: #1565C0;'>💸 Gestión de Fondos y Gastos</h2>", unsafe_allow_html=True)
    
    col_i1, col_i2, col_i3 = st.columns([2, 1, 1])
    nombres_cuentas = df_cuentas["Cuenta"].tolist() if not df_cuentas.empty else []
    
    with col_i1:
        opciones_inyec = ["TODAS"] + nombres_cuentas
        cuenta_inyec = st.selectbox("📥 Cuenta que recibe la inyección:", opciones_inyec)
        
        if cuenta_inyec != "TODAS":
            exc_c = df_excep[df_excep["Cuenta"] == cuenta_inyec]["Categoria_Excluida"].tolist() if not df_excep.empty else []
            nuevas_exc = st.multiselect(f"Excluir categorías en {cuenta_inyec}:", df_fijos["Categoría"].tolist(), default=exc_c)
            
            if st.button("💾 Guardar Excepciones"):
                df_temp = conn.read(spreadsheet=URL_GOOGLE_SHEET, worksheet="Excepciones").dropna(how="all")
                if not df_temp.empty:
                    df_temp = df_temp[df_temp["Cuenta"] != cuenta_inyec]
                nuevas_rows = pd.DataFrame([{"Cuenta": cuenta_inyec, "Categoria_Excluida": x} for x in nuevas_exc])
                df_final_excep = pd.concat([df_temp, nuevas_rows], ignore_index=True)
                conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Excepciones", data=df_final_excep)
                st.cache_data.clear()
                st.rerun()

    with col_i3:
        st.write("")
        # Botón para Agregar
        if st.button("➕ AGREGAR SEMANA", use_container_width=True, type="primary"):
            if not df_cuentas.empty and not df_fijos.empty:
                ctas_a_procesar = nombres_cuentas if cuenta_inyec == "TODAS" else [cuenta_inyec]
                for cta in ctas_a_procesar:
                    lista_negra = df_excep[df_excep["Cuenta"] == cta]["Categoria_Excluida"].tolist() if not df_excep.empty else []
                    cats_validas = df_fijos[~df_fijos["Categoría"].isin(lista_negra)].copy()
                    monto_total_cta = (pd.to_numeric(cats_validas["Monto_Mensual"]) / 4).sum()
                    
                    for idx, row in cats_validas.iterrows():
                        idx_f = df_fijos.index[df_fijos["Categoría"] == row["Categoría"]].tolist()[0]
                        df_fijos.at[idx_f, "Fondo_Disponible"] = float(df_fijos.at[idx_f, "Fondo_Disponible"]) + (float(row["Monto_Mensual"]) / 4)
                    
                    idx_c = df_cuentas.index[df_cuentas["Cuenta"] == cta].tolist()[0]
                    df_cuentas.at[idx_c, "Saldo"] = float(df_cuentas.at[idx_c, "Saldo"]) + monto_total_cta
                    
                    nuevo_mov = pd.DataFrame([{"Fecha": datetime.now().strftime("%Y-%m-%d"), "Cuenta": cta, "Concepto": "INYECCIÓN SEMANAL", "Monto": monto_total_cta}])
                    df_movs = pd.concat([df_movs, nuevo_mov], ignore_index=True)

                conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
                conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Cuentas", data=df_cuentas)
                conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Movimientos", data=df_movs)
                st.session_state.df_fijos, st.session_state.df_cuentas, st.session_state.df_movs = df_fijos, df_cuentas, df_movs
                st.rerun()

# Botón para Deshacer
        if st.button("↩️ DESHACER ÚLTIMA", use_container_width=True, help="Resta la última inyección semanal de los sobres y cuentas (incluso si queda en negativo)"):
            if not df_movs.empty and "INYECCIÓN SEMANAL" in df_movs["Concepto"].values:
                # 1. Identificamos la fecha de la última inyección realizada
                ult_fecha = df_movs[df_movs["Concepto"] == "INYECCIÓN SEMANAL"]["Fecha"].iloc[-1]
                inyec_a_revertir = df_movs[(df_movs["Concepto"] == "INYECCIÓN SEMANAL") & (df_movs["Fecha"] == ult_fecha)]
                
                for _, mov in inyec_a_revertir.iterrows():
                    cta = mov["Cuenta"]
                    monto_a_quitar = float(mov["Monto"])
                    
                    # RESTAR del saldo de la cuenta bancaria (permite negativos)
                    if cta in df_cuentas["Cuenta"].values:
                        idx_c = df_cuentas.index[df_cuentas["Cuenta"] == cta].tolist()[0]
                        df_cuentas.at[idx_c, "Saldo"] = float(df_cuentas.at[idx_c, "Saldo"]) - monto_a_quitar
                    
                    # RESTAR de los fondos/sobres individuales de forma forzada (permite negativos)
                    lista_negra = df_excep[df_excep["Cuenta"] == cta]["Categoria_Excluida"].tolist() if not df_excep.empty else []
                    cats_revertir = df_fijos[~df_fijos["Categoría"].isin(lista_negra)]
                    
                    for _, row in cats_revertir.iterrows():
                        idx_f = df_fijos.index[df_fijos["Categoría"] == row["Categoría"]].tolist()[0]
                        valor_semanal = float(row["Monto_Mensual"]) / 4
                        
                        # AQUÍ LA MAGIA: Resta directa, sea cual sea el valor actual, permitiendo que baje de cero
                        df_fijos.at[idx_f, "Fondo_Disponible"] = float(df_fijos.at[idx_f, "Fondo_Disponible"]) - valor_semanal

                # 2. Borrar los registros del historial para que no se dupliquen
                df_movs = df_movs.drop(inyec_a_revertir.index)
                
                # 3. Guardar cambios en Google Sheets y Memoria
                conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
                conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Cuentas", data=df_cuentas)
                conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Movimientos", data=df_movs)
                st.session_state.df_fijos, st.session_state.df_cuentas, st.session_state.df_movs = df_fijos, df_cuentas, df_movs
                
                st.success(f"Inyección del {ult_fecha} revertida con éxito. Fondos restados.")
                st.rerun()
    # --- SECCIÓN: REGISTRAR GASTO ---
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_g1, col_g2, col_g3, col_g4 = st.columns(4)
    with col_g1: c_gasto = st.selectbox("💳 Cuenta a Descontar:", nombres_cuentas)
    with col_g2: s_gasto = st.selectbox("📂 Categoría:", df_fijos["Categoría"].tolist() if not df_fijos.empty else [])
    with col_g3: m_gasto = st.number_input("💲 Monto a Restar:", min_value=0.0)
    with col_g4:
        st.write("")
        if st.button("APLICAR GASTO", use_container_width=True, type="primary"):
            if m_gasto > 0:
                fecha_h = datetime.now().strftime("%Y-%m-%d")
                
                # 1. Actualizar DataFrames en memoria
                nuevo_mov = pd.DataFrame([{"Fecha": fecha_h, "Cuenta": c_gasto, "Concepto": s_gasto, "Monto": -m_gasto}])
                df_movs = pd.concat([df_movs, nuevo_mov], ignore_index=True)
                
                idx_fijo = df_fijos.index[df_fijos["Categoría"] == s_gasto].tolist()[0]
                df_fijos.at[idx_fijo, "Fondo_Disponible"] = float(df_fijos.at[idx_fijo, "Fondo_Disponible"]) - m_gasto
                
                # 2. GUARDADO INMEDIATO EN GOOGLE SHEETS (Sincronización Total)
                conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Movimientos", data=df_movs)
                conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
                
                # 3. Actualizar Sesión y Refrescar
                st.session_state.df_movs = df_movs
                st.session_state.df_fijos = df_fijos
                st.success(f"Gasto de ${m_gasto:,.2f} aplicado y guardado.")
                st.rerun()
                
                # Actualizar Memoria de Sesión (Esto hace que sea instantáneo)
                st.session_state.df_movs = df_movs
                st.session_state.df_fijos = df_fijos
                
                st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)
    
    # --- HISTORIAL Y FONDOS ---
    cf1, cf2 = st.columns([1, 3])
    with cf1:
        st.markdown("<h4 style='color: #2E7D32;'>💰 Categorias Disponibles</h4>", unsafe_allow_html=True)
        if not df_fijos.empty:
            if "Fondo_Disponible" not in df_fijos.columns:
                df_fijos["Fondo_Disponible"] = 0.0
            df_fijos["Fondo_Disponible"] = pd.to_numeric(df_fijos["Fondo_Disponible"]).fillna(0)
        
        if not df_fijos.empty and "Categoría" in df_fijos.columns:
            # Tamaño exacto: cantidad de conceptos + 1 para los títulos
            altura_dinamica_sobres = (len(df_fijos) + 1) * 38
            st.dataframe(df_fijos[["Categoría", "Fondo_Disponible"]].style.format({"Fondo_Disponible": "${:,.0f}"}), use_container_width=True, height=altura_dinamica_sobres, hide_index=True)
        else:
            st.info("No hay categorías configuradas.")
    
    with cf2:
        l_filtros = ["VER TODO"] + (df_fijos["Categoría"].tolist() if not df_fijos.empty else [])
        f_sel = st.selectbox("📜 Selecciona un filtro para tu historial:", l_filtros)
        if not df_movs.empty:
            df_h = df_movs.sort_index(ascending=False) if f_sel == "VER TODO" else df_movs[df_movs["Concepto"] == f_sel].sort_index(ascending=False)
            st.dataframe(df_h, use_container_width=True, height=400, hide_index=True)
            if st.button("🗑️ ELIMINAR ÚLTIMO MOVIMIENTO"):
                if not df_movs.empty:
                    # Elimina la última fila real del dataframe original
                    df_movs = df_movs.drop(df_movs.index[-1])
                    conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Movimientos", data=df_movs)
                    st.cache_data.clear()
                    st.rerun()

# ---------------------------------------------------------
# NUEVA SECCIÓN: TRADING (Inversiones y Retiros)
# ---------------------------------------------------------
elif st.session_state.seccion == 'Trading':
    st.markdown("<h3 style='font-weight: 400; color: #555;'>📈 Gestión de Trading</h3>", unsafe_allow_html=True)
    
    # --- CÁLCULO SINCRONIZADO DE TRADING ---
    # 1. El dinero disponible SIEMPRE viene del sobre 'Inversion' de Gastos Fijos
    cap_disponible = 0.0
    if "Inversion" in df_fijos["Categoría"].values:
        idx_inv = df_fijos.index[df_fijos["Categoría"] == "Inversion"].tolist()[0]
        cap_disponible = float(df_fijos.at[idx_inv, "Fondo_Disponible"])

    # 2. Los otros totales sí vienen del historial de la hoja Trading
    cap_invertido = 0.0
    cap_retirado = 0.0
    if not df_trading.empty:
        df_trading["Monto"] = pd.to_numeric(df_trading["Monto"]).fillna(0)
        cap_invertido = df_trading[df_trading["Monto"] > 0]["Monto"].sum()
        cap_retirado = abs(df_trading[df_trading["Monto"] < 0]["Monto"].sum())

    # 3. Mostrar Métricas (Colores Rotados)
    col_k1, col_k2, col_k3 = st.columns(3)
    with col_k1:
        # Ahora es VERDE (Traído de "Enviado")
        st.markdown(f"""<div style="background-color: #1a1a1a; padding: 15px; border-radius: 10px; border-left: 5px solid #4CAF50;">
            <p style="margin:0; color: #888; font-size: 11px;">FONDO PARA INVERTIR (SOBRE)</p>
            <h3 style="margin:0; color: #4CAF50;">${cap_disponible:,.2f}</h3></div>""", unsafe_allow_html=True)
    with col_k2:
        # Ahora es ROJO (Traído de "Retirado")
        st.markdown(f"""<div style="background-color: #1a1a1a; padding: 15px; border-radius: 10px; border-left: 5px solid #F44336;">
            <p style="margin:0; color: #888; font-size: 11px;">TOTAL ENVIADO A TRADING</p>
            <h3 style="margin:0; color: #F44336;">${cap_invertido:,.2f}</h3></div>""", unsafe_allow_html=True)
    with col_k3:
        # Ahora es NARANJA (Traído de "Fondo")
        st.markdown(f"""<div style="background-color: #1a1a1a; padding: 15px; border-radius: 10px; border-left: 5px solid #F57C00;">
            <p style="margin:0; color: #888; font-size: 11px;">TOTAL RETIRADO DE TRADING</p>
            <h3 style="margin:0; color: #F57C00;">${cap_retirado:,.2f}</h3></div>""", unsafe_allow_html=True)
    st.write("")

    # Formulario de Movimiento con Conceptos Fijos
    col_t1, col_t2, col_t3, col_t4 = st.columns([2, 2, 2, 1])
    with col_t1: cta_t = st.selectbox("Cuenta Bancaria:", df_cuentas["Cuenta"].tolist() if not df_cuentas.empty else [])
    with col_t2: tipo_t = st.selectbox("Operación:", ["Inversión", "Retiro"])
    with col_t3: 
        lista_c = ["Trading View", "Cuenta de fondeo", "Fx Replay", "Mentoria", "OTRO"]
        c_sel_t = st.selectbox("Concepto:", lista_c)
        concepto_t = st.text_input("Escribe el concepto:") if c_sel_t == "OTRO" else c_sel_t
    with col_t4: monto_t = st.number_input("Monto ($):", min_value=0.0, step=100.0)
    
    # Creamos dos columnas: una ancha vacía a la izquierda y una pequeña a la derecha
    _, col_btn_op = st.columns([5, 1])
    with col_btn_op:
        btn_ejecutar = st.button("🚀 EJECUTAR OPERACIÓN", use_container_width=True, type="primary")
        
    if btn_ejecutar:
        if monto_t > 0:
            monto_trading = monto_t if tipo_t == "Inversión" else -monto_t
            monto_banco = -monto_t if tipo_t == "Inversión" else monto_t
            fecha_actual = datetime.now().strftime("%Y-%m-%d")
            
            # 1. Preparar datos de Trading e Historial General
            nueva_op = pd.DataFrame([{"Fecha": fecha_actual, "Cuenta": cta_t, "Tipo": tipo_t, "Concepto": concepto_t, "Monto": monto_trading}])
            df_trading = pd.concat([df_trading, nueva_op], ignore_index=True)
            
            nuevo_mov_gen = pd.DataFrame([{"Fecha": fecha_actual, "Cuenta": cta_t, "Concepto": f"TRADING: {concepto_t}", "Monto": monto_banco}])
            df_movs = pd.concat([df_movs, nuevo_mov_gen], ignore_index=True)
            
            # 2. Actualizar Saldo de la Cuenta Bancaria
            idx_cta = df_cuentas.index[df_cuentas["Cuenta"] == cta_t].tolist()[0]
            df_cuentas.at[idx_cta, "Saldo"] = float(df_cuentas.at[idx_cta, "Saldo"]) + monto_banco
            
            # 3. Si es Inversión, descontar del sobre "Inversion"
            if tipo_t == "Inversión" and "Inversion" in df_fijos["Categoría"].values:
                idx_inv = df_fijos.index[df_fijos["Categoría"] == "Inversion"].tolist()[0]
                df_fijos.at[idx_inv, "Fondo_Disponible"] = float(df_fijos.at[idx_inv, "Fondo_Disponible"]) - monto_t

            # 4. GUARDADO MASIVO INMEDIATO EN GOOGLE SHEETS
            conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Trading", data=df_trading)
            conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Movimientos", data=df_movs)
            conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Cuentas", data=df_cuentas)
            conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
            
            # 5. Actualizar la memoria de la sesión local para reflejar al instante
            st.session_state.df_trading = df_trading
            st.session_state.df_movs = df_movs
            st.session_state.df_cuentas = df_cuentas
            st.session_state.df_fijos = df_fijos
            
            st.success("Operación ejecutada y guardada al instante en todas las bases de datos.")
            st.rerun()

    if not df_trading.empty:
        st.markdown("---")
        st.markdown("**📝 Historial de Capital (Edición Directa)**")
        
        # Preparamos los datos con tipos compatibles
        df_edit_t = df_trading.copy()
        
        # Convertimos la columna Fecha a formato fecha real para que no de error
        if "Fecha" in df_edit_t.columns:
            df_edit_t["Fecha"] = pd.to_datetime(df_edit_t["Fecha"]).dt.date
        
        # Aseguramos que Monto sea numérico
        if "Monto" in df_edit_t.columns:
            df_edit_t["Monto"] = pd.to_numeric(df_edit_t["Monto"], errors='coerce').fillna(0.0)

        df_edit_t["🗑️"] = False
        
        # Editor de datos
        edited_df_t = st.data_editor(
            df_edit_t,
            use_container_width=True,
            hide_index=True,
            column_config={
                "🗑️": st.column_config.CheckboxColumn("Borrar", width="small"),
                "Monto": st.column_config.NumberColumn("Monto ($)", format="$%.2f"),
                "Tipo": st.column_config.SelectboxColumn("Operación", options=["Inversión", "Retiro"]),
                "Fecha": st.column_config.DateColumn("Fecha")
            }
        )

        # Igual aquí, usamos columnas para empujarlo a la derecha
        _, col_btn_hist = st.columns([9, 1])
        with col_btn_hist:
            btn_guardar = st.button("💾 GUARDAR CAMBIOS EN HISTORIAL", use_container_width=True, type="primary")
            
        if btn_guardar:
            # 1. REVERSIÓN TOTAL DE LO QUE HABÍA ANTES
            # (Anulamos el efecto de todos los movimientos actuales en la memoria para 'empezar de cero')
            for _, fila_vieja in st.session_state.df_trading.iterrows():
                cta_v = fila_vieja["Cuenta"]
                m_v = float(fila_vieja["Monto"])
                tipo_v = fila_vieja["Tipo"]
                
                # Devolvemos saldo al banco
                if cta_v in df_cuentas["Cuenta"].values:
                    idx_c = df_cuentas.index[df_cuentas["Cuenta"] == cta_v].tolist()[0]
                    df_cuentas.at[idx_c, "Saldo"] = float(df_cuentas.at[idx_c, "Saldo"]) - m_v
                
                # Devolvemos saldo al sobre de Inversion (si era inversión)
                if tipo_v == "Inversión" and "Inversion" in df_fijos["Categoría"].values:
                    idx_i = df_fijos.index[df_fijos["Categoría"] == "Inversion"].tolist()[0]
                    df_fijos.at[idx_i, "Fondo_Disponible"] = float(df_fijos.at[idx_i, "Fondo_Disponible"]) + abs(m_v)

            # 2. APLICAR LOS NUEVOS DATOS (EDITADOS)
            # Solo procesamos las filas que NO marcaste para borrar
            df_final_t = edited_df_t[edited_df_t["🗑️"] == False].drop(columns=["🗑️"])
            
            for _, fila_nueva in df_final_t.iterrows():
                cta_n = fila_nueva["Cuenta"]
                m_n = float(fila_nueva["Monto"])
                tipo_n = fila_nueva["Tipo"]
                
                # Aplicamos nuevo saldo al banco
                if cta_n in df_cuentas["Cuenta"].values:
                    idx_c = df_cuentas.index[df_cuentas["Cuenta"] == cta_n].tolist()[0]
                    df_cuentas.at[idx_c, "Saldo"] = float(df_cuentas.at[idx_c, "Saldo"]) + m_n
                
                # Aplicamos nuevo descuento al sobre de Inversion
                if tipo_n == "Inversión" and "Inversion" in df_fijos["Categoría"].values:
                    idx_i = df_fijos.index[df_fijos["Categoría"] == "Inversion"].tolist()[0]
                    df_fijos.at[idx_i, "Fondo_Disponible"] = float(df_fijos.at[idx_i, "Fondo_Disponible"]) - abs(m_n)

            # 3. GUARDAR TODO EN GOOGLE SHEETS Y REFRESCAR
            if "Fecha" in df_final_t.columns:
                df_final_t["Fecha"] = df_final_t["Fecha"].astype(str)
            
            conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Trading", data=df_final_t)
            conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Cuentas", data=df_cuentas)
            conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
            
            # Actualizamos memoria local
            st.session_state.df_trading = df_final_t
            st.session_state.df_cuentas = df_cuentas
            st.session_state.df_fijos = df_fijos
            
            st.success("¡Historial y balances actualizados correctamente!")
            st.rerun()

# ---------------------------------------------------------
# 4. CUENTAS (Compacto y Minimalista)
# ---------------------------------------------------------
elif st.session_state.seccion == 'Cuentas':
    st.write("") 
    
    if not df_cuentas.empty and not df_fijos.empty:
        # Convertimos a número ignorando errores (lo que no sea número será 0)
        fondos_limpios = pd.to_numeric(df_fijos["Fondo_Disponible"], errors='coerce').fillna(0)
        t_total = fondos_limpios.sum()
        
        st.markdown(f"""
            <div style="background: linear-gradient(90deg, #0F2027 0%, #2C5364 100%); 
                        padding: 15px; border-radius: 12px; text-align: center; color: white; 
                        margin-bottom: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
                <p style="margin: 0; font-size: 11px; letter-spacing: 2px; color: #b0bec5; font-weight: 600;">BALANCE TOTAL FONDOS</p>
                <h1 style="margin: 0; font-size: 38px; font-weight: 700;">${t_total:,.2f}</h1>
            </div>
        """, unsafe_allow_html=True)
        
        cols = st.columns(4)
        colores_neon = ["#00E5FF", "#B388FF", "#FF8A80", "#69F0AE", "#FFD180", "#82B1FF"]
        
        for i, (index, row) in enumerate(df_cuentas.iterrows()):
            # Filtramos categorías que NO están en la lista de excepciones de esta cuenta
            excluidas = df_excep[df_excep["Cuenta"] == row['Cuenta']]["Categoria_Excluida"].tolist() if not df_excep.empty else []
            
            # Sumamos solo los fondos de las categorías permitidas
            mask = ~df_fijos["Categoría"].isin(excluidas)
            saldo_calculado = pd.to_numeric(df_fijos.loc[mask, "Fondo_Disponible"], errors='coerce').fillna(0).sum()
            
            color_acento = colores_neon[i % len(colores_neon)]
            with cols[i % 4]:
                st.markdown(f"""
                    <div style="background-color: rgba(255, 255, 255, 0.05); padding: 18px; 
                                border-radius: 10px; border-top: 3px solid {color_acento}; 
                                margin-bottom: 15px; box-shadow: 2px 4px 10px rgba(0,0,0,0.2);">
                        <p style="margin: 0; font-size: 10px; text-transform: uppercase; font-weight: 700; opacity: 0.6;">{row['Cuenta']}</p>
                        <h4 style="margin: 5px 0 0 0; font-size: 20px; font-weight: 400;">${saldo_calculado:,.2f}</h4>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Aún no tienes cuentas registradas.")

    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Menú oculto en un expander para no ensuciar la pantalla
    with st.expander("⚙️ Administrar Cuentas", expanded=False):
        col_e1, col_e2 = st.columns(2)
        
        with col_e1:
            st.markdown("<p style='color:#666; font-size:14px; margin-bottom:5px;'><b>Crear o Modificar</b></p>", unsafe_allow_html=True)
            opc = ["➕ NUEVA CUENTA"] + (df_cuentas["Cuenta"].tolist() if not df_cuentas.empty else [])
            c_edit = st.selectbox("Selecciona:", opc, label_visibility="collapsed")
            
            s_base = float(df_cuentas.loc[df_cuentas["Cuenta"] == c_edit, "Saldo"].values[0]) if c_edit != "➕ NUEVA CUENTA" else 0.0
            n_nombre = st.text_input("Nombre de la cuenta:", placeholder="Ej: Efectivo") if c_edit == "➕ NUEVA CUENTA" else c_edit
            n_saldo = st.number_input("Saldo Actual:", value=s_base, step=100.0)
            
            if st.button("Guardar Cambios", use_container_width=True):
                if n_nombre:
                    if not df_cuentas.empty and n_nombre in df_cuentas["Cuenta"].values:
                        df_cuentas.loc[df_cuentas["Cuenta"] == n_nombre, "Saldo"] = n_saldo
                    else:
                        df_cuentas = pd.concat([df_cuentas, pd.DataFrame([{"Cuenta": n_nombre, "Saldo": n_saldo}])], ignore_index=True)
                    conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Cuentas", data=df_cuentas)
                    st.cache_data.clear()
                    st.rerun()

        with col_e2:
            st.markdown("<p style='color:#666; font-size:14px; margin-bottom:5px;'><b>Eliminar Cuenta</b></p>", unsafe_allow_html=True)
            if not df_cuentas.empty:
                c_del = st.selectbox("Borrar:", df_cuentas["Cuenta"].tolist(), label_visibility="collapsed")
                st.write("") # Espaciador
                st.write("") # Espaciador
                if st.button("Eliminar Permanentemente", use_container_width=True):
                    df_cuentas = df_cuentas[df_cuentas["Cuenta"] != c_del]
                    conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Cuentas", data=df_cuentas)
                    st.cache_data.clear()
                    st.rerun()