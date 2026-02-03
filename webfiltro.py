import os
import pandas as pd
import streamlit as st
from io import BytesIO
from PIL import Image

# Configuração de estilo CSS
CUSTOM_CSS = """
<style>
    [data-testid="stSidebar"] { background-color: #a3cbc1; }
    .stButton>button {
        background-color: #57a4a5; color: white; border: none; border-radius: 8px; font-weight: 600;
    }
    .stButton>button:hover { background-color: #468e8f; color: white; }
    [data-testid="stFileUploader"] {
        background-color: #f0f7f6; border: 1px dashed #57a4a5; border-radius: 8px; padding: 15px;
    }
    h1, h2, h3 { color: #2c3e50; }
    [data-testid="stSidebar"] * { color: #ffffff; font-weight: 500; }
</style>
"""

def get_excel_buffer(df):
    """Gera buffer do Excel para download."""
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return buffer

def main():
    st.set_page_config(page_title="Hidrosedi - Tools", page_icon="💧", layout="centered")
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    # Header Layout
    c1, c2 = st.columns([1, 4])
    with c1:
        if os.path.exists("hidrosedi.jpg"):
            st.image(Image.open("hidrosedi.jpg"), use_container_width=True)
    with c2:
        st.title("Filtragem de Planilhas")
        st.markdown("<h5 style='color: #57a4a5;'>Processamento de Dados Hidrológicos</h5>", unsafe_allow_html=True)

    # Sidebar
    st.sidebar.markdown("### Configuração")
    mode = st.sidebar.radio(
        "Método:",
        ("Horas Exatas (00 min)", "Regularização (Nearest)")
    )
    
    st.sidebar.markdown("---")
    if "Exatas" in mode:
        st.sidebar.info("Filtra apenas registros com minuto 00.")
    else:
        st.sidebar.info("Ajusta registros para a hora cheia mais próxima.")

    # Main App
    st.write("")
    st.markdown("### Carregue seu arquivo")
    uploaded = st.file_uploader("Arquivo .csv (separador ;)", type=['csv'])

    if uploaded:
        st.markdown("### Resultado")
        try:
            # Load Data
            df = pd.read_csv(uploaded, sep=';', dayfirst=True)
            
            # Datetime conversion handling
            try:
                df['Data'] = pd.to_datetime(df['Data'], dayfirst=True)
            except ValueError:
                df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y %H:%M')
            
            df = df.sort_values('Data')

            # Processing
            if "Exatas" in mode:
                res = df[df['Data'].dt.minute == 0].copy()
            else:
                grid = pd.date_range(
                    start=df['Data'].min().floor('h'),
                    end=df['Data'].max().ceil('h'),
                    freq='h'
                )
                res = pd.merge_asof(pd.DataFrame({'Data': grid}), df, on='Data', direction='nearest')

            # Formatting
            res['Data'] = res['Data'].dt.strftime('%d/%m/%Y %H:%M')

            # Output
            st.success(f"Processado com sucesso. {len(res)} registros gerados.")
            st.dataframe(res.head(), use_container_width=True)

            st.download_button(
                label="📥 Baixar Excel (.xlsx)",
                data=get_excel_buffer(res),
                file_name="hidrosedi_filtrado.xlsx",
                mime="application/vnd.ms-excel"
            )

        except Exception as e:
            st.error(f"Erro na execução: {e}")

if __name__ == "__main__":
    main()