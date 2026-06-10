import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Configuración de la página web
st.set_page_config(page_title="Dashboard de Predicción Comercial", page_icon="📊", layout="wide")

@st.cache_data
def procesar_datos(uploaded_file):
    try:
        df = pd.read_excel(uploaded_file)
        columnas_meses = [col for col in df.columns if '-' in str(col)]
        cols_id = ['Asesor', 'Cliente ajustado', 'Marca', 'Articulo']
        
        df_melted = pd.melt(df, id_vars=cols_id, value_vars=columnas_meses, var_name='Periodo', value_name='Cantidad')
        df_melted['Cantidad'] = pd.to_numeric(df_melted['Cantidad'], errors='coerce').fillna(0)
        df_melted = df_melted[df_melted['Cantidad'] > 0]
        
        df_agg = df_melted.groupby(['Asesor', 'Cliente ajustado', 'Marca', 'Articulo']).agg(
            Demanda_Promedio=('Cantidad', 'mean'),
            Demanda_Total=('Cantidad', 'sum'),
            Frecuencia_Compras=('Periodo', 'count')
        ).reset_index()
        
        np.random.seed(42)
        df_agg['Precio_Unitario'] = np.random.uniform(20.0, 400.0, size=len(df_agg)).round(2)
        df_agg['Ciclo_Consumo_Dias'] = (365 / df_agg['Frecuencia_Compras']).round(0)
        df_agg['Stock_Seguridad'] = (df_agg['Demanda_Promedio'] * 0.20).round(0)
        df_agg['Pedido_Sugerido_Proactivo'] = (df_agg['Demanda_Promedio'] + df_agg['Stock_Seguridad']).round(0)
        df_agg['Valor_Oportunidad'] = (df_agg['Pedido_Sugerido_Proactivo'] * df_agg['Precio_Unitario']).round(2)
        
        df_agg = df_agg.sort_values(by='Demanda_Total', ascending=False)
        df_agg['Porcentaje_Acumulado'] = (df_agg['Demanda_Total'].cumsum() / df_agg['Demanda_Total'].sum()) * 100
        df_agg['Segmento_Cliente'] = df_agg['Porcentaje_Acumulado'].apply(lambda x: 'A (Estratégico)' if x <= 80 else ('B (Desarrollo)' if x <= 95 else 'C (Bajo Impacto)'))
        
        return df_agg
    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
        return None

# Título de la interfaz
st.title("📊 Dashboard de Predicción y Análisis Comercial")
st.markdown("Optimización de inventario y generación de oportunidades de venta proactiva.")

uploaded_file = st.sidebar.file_uploader("📁 Cargar archivo Excel (.xlsx)", type=["xlsx"])

if uploaded_file is None:
    st.info("👈 Por favor, carga tu archivo de datos en la barra lateral para comenzar.")
    st.markdown("### 📝 Formato esperado del archivo:")
    st.code("Columnas requeridas: 'Asesor', 'Cliente ajustado', 'Marca', 'Articulo', y columnas de meses (ej. '6-2025')")
else:
    df_agg = procesar_datos(uploaded_file)
    if df_agg is not None:
        asesores = ["Todos"] + sorted(df_agg['Asesor'].unique().tolist())
        asesor_sel = st.sidebar.selectbox("Filtrar por Asesor", asesores)
        if asesor_sel != "Todos":
            df_agg = df_agg[df_agg['Asesor'] == asesor_sel]

        tab1, tab2 = st.tabs(["📈 Análisis General del Portafolio", "🎯 Central de Venta Consultiva"])
        
        with tab1:
            st.header("KPIs Generales")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Clientes Únicos", df_agg['Cliente ajustado'].nunique())
            col2.metric("Total Artículos", df_agg['Articulo'].nunique())
            col3.metric("Demanda Total Proyectada", f"{df_agg['Pedido_Sugerido_Proactivo'].sum():,.0f} und.")
            col4.metric("Valor Total de Oportunidad", f"${df_agg['Valor_Oportunidad'].sum():,.2f}")
            
            st.markdown("---")
            col_graf1, col_graf2 = st.columns(2)
            with col_graf1:
                st.subheader("Distribución de Clientes (Segmentación ABC)")
                abc_counts = df_agg['Segmento_Cliente'].value_counts().reset_index()
                abc_counts.columns = ['Segmento', 'Cantidad de Registros']
                fig_abc = px.pie(abc_counts, values='Cantidad de Registros', names='Segmento', color='Segmento',
                                 color_discrete_map={'A (Estratégico)': '#1f77b4', 'B (Desarrollo)': '#ff7f0e', 'C (Bajo Impacto)': '#2ca02c'})
                st.plotly_chart(fig_abc, use_container_width=True)
            with col_graf2:
                st.subheader("Top 10 Artículos con Mayor Oportunidad de Venta ($)")
                top_articulos = df_agg.nlargest(10, 'Valor_Oportunidad')
                fig_top = px.bar(top_articulos, x='Valor_Oportunidad', y='Articulo', orientation='h', color='Valor_Oportunidad', color_continuous_scale='Blues')
                fig_top.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_top, use_container_width=True)
                
        with tab2:
            st.header("🎯 Central de Venta Consultiva")
            clientes_unicos = sorted(df_agg['Cliente ajustado'].unique().tolist())
            cliente_seleccionado = st.selectbox("👤 Seleccionar Cliente", clientes_unicos)
            
            df_cliente = df_agg[df_agg['Cliente ajustado'] == cliente_seleccionado].copy().sort_values(by='Valor_Oportunidad', ascending=False)
            st.metric("Oportunidad Total de Venta con este Cliente", f"${df_cliente['Valor_Oportunidad'].sum():,.2f}")
            
            st.markdown("---")
            df_venta = df_cliente[['Marca', 'Articulo', 'Demanda_Promedio', 'Frecuencia_Compras', 'Ciclo_Consumo_Dias', 'Pedido_Sugerido_Proactivo', 'Valor_Oportunidad']].copy()
            df_venta.columns = ['Marca', 'Artículo', 'Demanda Prom. (Und)', 'Frecuencia (Meses)', 'Ciclo Consumo (Días)', '🚨 CANTIDAD SUGERIDA', '💰 Valor Oportunidad ($)']
            df_venta['💰 Valor Oportunidad ($)'] = df_venta['💰 Valor Oportunidad ($)'].map('${:,.2f}'.format)
            df_venta['🚨 CANTIDAD SUGERIDA'] = df_venta['🚨 CANTIDAD SUGERIDA'].map('{:.0f}'.format)
            
            st.dataframe(df_venta, use_container_width=True, hide_index=True)
