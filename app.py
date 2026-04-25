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

if not df_fijos.empty and "Fondo_Disponible" not in df_fijos.columns:
    df_fijos["Fondo_Disponible"] = 0.0

# --- NAVEGACIÓN ---
st.markdown("<h1 style='text-align: center; color: #4CAF50;'>💰 MI CENTRO FINANCIERO</h1>", unsafe_allow_html=True)
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
# NUEVA SECCIÓN: TRADING
# ---------------------------------------------------------
elif st.session_state.seccion == 'Trading':
    st.markdown("<h2 style='color: #F57C00;'>📈 Panel de Trading</h2>", unsafe_allow_html=True)
    st.info("¡Bienvenido a tu panel de Trading! Aquí construiremos tu nueva herramienta.")

# ---------------------------------------------------------
# 4. CUENTAS (Minimalista y Elegante)
# ---------------------------------------------------------
elif st.session_state.seccion == 'Cuentas':
    st.markdown("<h3 style='font-weight: 400; color: #555; margin-bottom: 0;'>Mis Cuentas</h3>", unsafe_allow_html=True)
    
    if not df_cuentas.empty:
        df_cuentas["Saldo"] = pd.to_numeric(df_cuentas["Saldo"]).fillna(0)
        t_total = df_cuentas["Saldo"].sum()
        
        # Total gigante, sin fondo, muy limpio
        st.markdown(f"""
            <div style="text-align: center; margin-top: 20px; margin-bottom: 40px;">
                <p style="color: #888; font-size: 13px; text-transform: uppercase; letter-spacing: 1.5px; margin: 0;">Total Disponible</p>
                <h1 style="color: #111; font-size: 55px; font-weight: 300; margin: 0; letter-spacing: -1px;">${t_total:,.2f}</h1>
            </div>
        """, unsafe_allow_html=True)
        
        # Tarjetas sutiles, solo con un borde gris clarito
        cols = st.columns(4)
        for i, (index, row) in enumerate(df_cuentas.iterrows()):
            with cols[i % 4]:
                st.markdown(f"""
                    <div style="border: 1px solid #eaeaea; border-radius: 8px; padding: 20px; text-align: center; margin-bottom: 15px;">
                        <p style="color: #999; font-size: 12px; margin: 0; text-transform: uppercase; letter-spacing: 0.5px;">{row['Cuenta']}</p>
                        <h4 style="color: #333; font-size: 22px; font-weight: 400; margin: 5px 0 0 0;">${row['Saldo']:,.2f}</h4>
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