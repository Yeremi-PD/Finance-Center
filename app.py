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
df_excep = cargar_hoja("Excepciones")
df_trading = cargar_hoja("Trading") # Nueva hoja cargada

if not df_fijos.empty and "Fondo_Disponible" not in df_fijos.columns:
    df_fijos["Fondo_Disponible"] = 0.0

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
        if st.button("➕ AGREGAR OTRA SEMANA", use_container_width=True, type="primary"):
            if not df_cuentas.empty and not df_fijos.empty:
                ctas_a_procesar = nombres_cuentas if cuenta_inyec == "TODAS" else [cuenta_inyec]
                
                for cta in ctas_a_procesar:
                    excepciones_de_esta_cta = df_excep[df_excep["Cuenta"] == cta]["Categoria_Excluida"].tolist() if not df_excep.empty else []
                    cats_validas = df_fijos[~df_fijos["Categoría"].isin(excepciones_de_esta_cta)].copy()
                    monto_total_cta = (pd.to_numeric(cats_validas["Monto_Mensual"]) / 4).sum()
                    
                    for idx, row in cats_validas.iterrows():
                        f_actual = pd.to_numeric(df_fijos.loc[df_fijos["Categoría"] == row["Categoría"], "Fondo_Disponible"]).values[0]
                        df_fijos.loc[df_fijos["Categoría"] == row["Categoría"], "Fondo_Disponible"] = f_actual + (pd.to_numeric(row["Monto_Mensual"]) / 4)
                    
                    s_banco = float(df_cuentas.loc[df_cuentas["Cuenta"] == cta, "Saldo"].values[0])
                    df_cuentas.loc[df_cuentas["Cuenta"] == cta, "Saldo"] = s_banco + monto_total_cta
                    
                    fecha_h = datetime.now().strftime("%Y-%m-%d")
                    nuevo_ingreso = pd.DataFrame([{"Fecha": fecha_h, "Cuenta": cta, "Concepto": "INYECCIÓN SEMANAL", "Monto": monto_total_cta}])
                    df_movs = pd.concat([df_movs, nuevo_ingreso], ignore_index=True)

                conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
                conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Cuentas", data=df_cuentas)
                conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Movimientos", data=df_movs)
                st.cache_data.clear()
                st.rerun()

    # --- SECCIÓN: REGISTRAR GASTO ---
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_g1, col_g2, col_g3, col_g4 = st.columns(4)
    with col_g1: c_gasto = st.selectbox("💳 Cuenta a Descontar:", nombres_cuentas)
    with col_g2: s_gasto = st.selectbox("📂 Sobre / Categoría:", df_fijos["Categoría"].tolist() if not df_fijos.empty else [])
    with col_g3: m_gasto = st.number_input("💲 Monto a Restar:", min_value=0.0)
    with col_g4:
        st.write("")
        if st.button("🔴 EJECUTAR GASTO", use_container_width=True):
            if m_gasto > 0:
                fecha_h = datetime.now().strftime("%Y-%m-%d")
                df_movs = pd.concat([df_movs, pd.DataFrame([{"Fecha": fecha_h, "Cuenta": c_gasto, "Concepto": s_gasto, "Monto": -m_gasto}])], ignore_index=True)
                df_cuentas.loc[df_cuentas["Cuenta"] == c_gasto, "Saldo"] = float(df_cuentas.loc[df_cuentas["Cuenta"] == c_gasto, "Saldo"]) - m_gasto
                df_fijos.loc[df_fijos["Categoría"] == s_gasto, "Fondo_Disponible"] = float(df_fijos.loc[df_fijos["Categoría"] == s_gasto, "Fondo_Disponible"]) - m_gasto
                
                conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Movimientos", data=df_movs)
                conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Cuentas", data=df_cuentas)
                conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Gastos_Fijos", data=df_fijos)
                st.cache_data.clear()
                st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)
    
    # --- HISTORIAL Y FONDOS ---
    cf1, cf2 = st.columns([1, 3])
    with cf1:
        st.markdown("<h4 style='color: #2E7D32;'>💰 Sobres Disponibles</h4>", unsafe_allow_html=True)
        df_fijos["Fondo_Disponible"] = pd.to_numeric(df_fijos["Fondo_Disponible"]).fillna(0)
        
        # Tamaño exacto: cantidad de conceptos + 1 para los títulos
        altura_dinamica_sobres = (len(df_fijos) + 1) * 38
        
        st.dataframe(df_fijos[["Categoría", "Fondo_Disponible"]].style.format({"Fondo_Disponible": "${:,.0f}"}), use_container_width=True, height=altura_dinamica_sobres, hide_index=True)
    
    with cf2:
        l_filtros = ["VER TODO"] + (df_fijos["Categoría"].tolist() if not df_fijos.empty else [])
        f_sel = st.selectbox("📜 Selecciona un filtro para tu historial:", l_filtros)
        if not df_movs.empty:
            df_h = df_movs.sort_index(ascending=False) if f_sel == "VER TODO" else df_movs[df_movs["Concepto"] == f_sel].sort_index(ascending=False)
            st.dataframe(df_h, use_container_width=True, height=450, hide_index=True)

# ---------------------------------------------------------
# NUEVA SECCIÓN: TRADING (Inversiones y Retiros)
# ---------------------------------------------------------
elif st.session_state.seccion == 'Trading':
    st.markdown("<h3 style='font-weight: 400; color: #555;'>📈 Gestión de Cartera Trading</h3>", unsafe_allow_html=True)
    
    # Cálculo de Balance de Trading Detallado
    if not df_trading.empty:
        df_trading["Monto"] = pd.to_numeric(df_trading["Monto"]).fillna(0)
        cap_disponible = df_trading["Monto"].sum()
        cap_invertido = df_trading[df_trading["Monto"] > 0]["Monto"].sum()
        cap_retirado = abs(df_trading[df_trading["Monto"] < 0]["Monto"].sum())

        col_k1, col_k2, col_k3 = st.columns(3)
        with col_k1:
            st.markdown(f"""<div style="background-color: #1a1a1a; padding: 15px; border-radius: 10px; border-left: 5px solid #F57C00;">
                <p style="margin:0; color: #888; font-size: 11px;">DINERO DISPONIBLE</p>
                <h3 style="margin:0; color: #F57C00;">${cap_disponible:,.2f}</h3></div>""", unsafe_allow_html=True)
        with col_k2:
            st.markdown(f"""<div style="background-color: #1a1a1a; padding: 15px; border-radius: 10px; border-left: 5px solid #4CAF50;">
                <p style="margin:0; color: #888; font-size: 11px;">CAPITAL INVERTIDO</p>
                <h3 style="margin:0; color: #4CAF50;">${cap_invertido:,.2f}</h3></div>""", unsafe_allow_html=True)
        with col_k3:
            st.markdown(f"""<div style="background-color: #1a1a1a; padding: 15px; border-radius: 10px; border-left: 5px solid #F44336;">
                <p style="margin:0; color: #888; font-size: 11px;">CAPITAL RETIRADO</p>
                <h3 style="margin:0; color: #F44336;">${cap_retirado:,.2f}</h3></div>""", unsafe_allow_html=True)
    st.write("")

    # Formulario de Movimiento con Conceptos Fijos
    col_t1, col_t2, col_t3, col_t4 = st.columns([2, 2, 2, 1])
    with col_t1: cta_t = st.selectbox("Cuenta Bancaria:", df_cuentas["Cuenta"].tolist() if not df_cuentas.empty else [])
    with col_t2: tipo_t = st.selectbox("Operación:", ["Inversión (Sale de Banco)", "Retiro (Entra a Banco)"])
    with col_t3: 
        lista_c = ["Trading View", "Cuenta de fondeo", "fx replay", "mentoria", "OTRO"]
        c_sel_t = st.selectbox("Concepto:", lista_c)
        concepto_t = st.text_input("Escribe el concepto:") if c_sel_t == "OTRO" else c_sel_t
    with col_t4: monto_t = st.number_input("Monto ($):", min_value=0.0, step=100.0)
    
    if st.button("🚀 EJECUTAR OPERACIÓN", use_container_width=True, type="primary"):
        if monto_t > 0:
            # Lógica: Inversión suma a Trading y resta a Banco. Retiro es al revés.
            monto_trading = monto_t if "Inversión" in tipo_t else -monto_t
            monto_banco = -monto_t if "Inversión" in tipo_t else monto_t
            
            # 1. Guardar en Trading
            nueva_op = pd.DataFrame([{"Fecha": datetime.now().strftime("%Y-%m-%d"), "Cuenta": cta_t, "Tipo": tipo_t, "Concepto": concepto_t, "Monto": monto_trading}])
            df_trading = pd.concat([df_trading, nueva_op], ignore_index=True)
            conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Trading", data=df_trading)
            
            # 2. Actualizar Saldo de Cuenta Bancaria
            saldo_act = float(df_cuentas.loc[df_cuentas["Cuenta"] == cta_t, "Saldo"].values[0])
            df_cuentas.loc[df_cuentas["Cuenta"] == cta_t, "Saldo"] = saldo_act + monto_banco
            conn.update(spreadsheet=URL_GOOGLE_SHEET, worksheet="Cuentas", data=df_cuentas)
            
            st.cache_data.clear()
            st.rerun()

    if not df_trading.empty:
        st.markdown("---")
        col_h1, col_h2 = st.columns([2, 1])
        with col_h1: st.markdown("**Historial de Capital Trading**")
        with col_h2: f_t = st.selectbox("Filtrar historial:", ["VER TODO", "Inversiones", "Retiros"], label_visibility="collapsed")
        
        # Lógica de Filtrado
        df_t_final = df_trading.copy()
        if f_t == "Inversiones":
            df_t_final = df_trading[df_trading["Monto"] > 0]
        elif f_t == "Retiros":
            df_t_final = df_trading[df_trading["Monto"] < 0]
            
        st.dataframe(df_t_final.sort_index(ascending=False), use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# 4. CUENTAS (Compacto y Minimalista)
# ---------------------------------------------------------
elif st.session_state.seccion == 'Cuentas':
    st.write("") 
    
    if not df_cuentas.empty:
        df_cuentas["Saldo"] = pd.to_numeric(df_cuentas["Saldo"]).fillna(0)
        t_total = df_cuentas["Saldo"].sum()
        
        # Banner Total Compacto
        st.markdown(f"""
            <div style="background: linear-gradient(90deg, #0F2027 0%, #2C5364 100%); 
                        padding: 15px; border-radius: 12px; text-align: center; color: white; 
                        margin-bottom: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
                <p style="margin: 0; font-size: 11px; letter-spacing: 2px; color: #b0bec5; font-weight: 600;">BALANCE TOTAL</p>
                <h1 style="margin: 0; font-size: 38px; font-weight: 700;">${t_total:,.2f}</h1>
            </div>
        """, unsafe_allow_html=True)
        
        # Grid de Cuentas con fondo resaltado
        cols = st.columns(4)
        colores_neon = ["#00E5FF", "#B388FF", "#FF8A80", "#69F0AE", "#FFD180", "#82B1FF"]
        
        for i, (index, row) in enumerate(df_cuentas.iterrows()):
            color_acento = colores_neon[i % len(colores_neon)]
            with cols[i % 4]:
                st.markdown(f"""
                    <div style="background-color: rgba(255, 255, 255, 0.05); padding: 18px; 
                                border-radius: 10px; border-top: 3px solid {color_acento}; 
                                margin-bottom: 15px; border-right: 1px solid rgba(255,255,255,0.05);
                                border-bottom: 1px solid rgba(255,255,255,0.05); box-shadow: 2px 4px 10px rgba(0,0,0,0.2);">
                        <p style="margin: 0; font-size: 10px; text-transform: uppercase; font-weight: 700; opacity: 0.6;">{row['Cuenta']}</p>
                        <h4 style="margin: 5px 0 0 0; font-size: 20px; font-weight: 400;">${row['Saldo']:,.2f}</h4>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Aún no tienes cuentas registradas.")

    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Menú oculto en un expander para no ensuciar la pantalla
    with st.expander("⚙️ Administrar Cuentas (Crear, Editar o Eliminar)", expanded=False):
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