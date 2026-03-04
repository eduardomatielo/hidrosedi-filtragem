import os
import pandas as pd
import streamlit as st
from io import BytesIO
from PIL import Image

# Configuração de estilo CSS (Clean & Corporate)
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

    # --- SECURITY CHECK ---
    # password = st.sidebar.text_input("Chave de Acesso", type="password")
    # if password != "hidro2026":
    #     st.sidebar.warning("Acesso restrito.")
    #     st.stop()

    # Header
    c1, c2 = st.columns([1, 4])
    with c1:
        if os.path.exists("hidrosedi.jpg"):
            st.image(Image.open("hidrosedi.jpg"), use_container_width=True)
    with c2:
        st.title("Filtragem de Planilhas")
        st.markdown("<h5 style='color: #57a4a5;'>Processamento de Dados Hidrológicos</h5>", unsafe_allow_html=True)

    # Sidebar Config
    st.sidebar.markdown("### Configuração")

    mode = st.sidebar.radio(
        "Método de Filtragem:",
        ("Horas Exatas (00 min)", "Regularização (Nearest)")
    )
    
    st.sidebar.markdown("---")
    st.sidebar.info("Reconhecimento automático:\n- .dat (Tabulação)\n- .csv / .txt (Vírgula)")

    # Main App
    st.write("")
    st.markdown("### Carregue seu arquivo")
    
    uploaded = st.file_uploader("Arquivo de dados", type=['csv', 'dat', 'txt'])

    if uploaded:
        st.markdown("---")
        try:
            # 1. Identificar a extensão e definir o separador
            file_ext = uploaded.name.split('.')[-1].lower()
            if file_ext == 'dat':
                delimiter = '\t'
            else:
                delimiter = ','
            
            # 2. Carregar os dados
            df = pd.read_csv(uploaded, sep=delimiter, dayfirst=True)
            
            # 3. Forçar a primeira coluna a ser 'Data'
            primeira_coluna = df.columns[0]
            df = df.rename(columns={primeira_coluna: 'Data'})

            # 4. Preview opcional dos dados crus (antes de filtrar)
            with st.expander("👀 Ver arquivo original sem formatação"):
                st.dataframe(df.head(15), use_container_width=True)

            # Datetime conversion
            try:
                df['Data'] = pd.to_datetime(df['Data'], dayfirst=True)
            except ValueError:
                df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y %H:%M', errors='coerce')
            
            df = df.dropna(subset=['Data'])
            df = df.sort_values('Data')

            # Processing Logic
            if "Exatas" in mode:
                res = df[df['Data'].dt.minute == 0].copy()
            else:
                grid = pd.date_range(
                    start=df['Data'].min().floor('h'),
                    end=df['Data'].max().ceil('h'),
                    freq='h'
                )
                res = pd.merge_asof(pd.DataFrame({'Data': grid}), df, on='Data', direction='nearest')

            # Formatting para manter o visual limpo no Excel
            res['Data'] = res['Data'].dt.strftime('%d/%m/%Y %H:%M')

            # Output e Pré-visualização Final
            st.success(f"Filtragem concluída! Total de registros: {len(res)}")
            
            st.markdown("#### Pré-visualização da Planilha Filtrada")
            # st.dataframe exibe uma tabela interativa estilo Excel com barra de rolagem
            st.dataframe(res, use_container_width=True, height=350) 

            st.download_button(
                label="📥 Baixar Excel (.xlsx)",
                data=get_excel_buffer(res),
                file_name="hidrosedi_filtrado.xlsx",
                mime="application/vnd.ms-excel"
            )

        except Exception as e:
            st.error(f"Erro de Processamento: {e}")
            st.info("Dica: Verifique se o arquivo não está corrompido ou se possui formatações fora do padrão.")

if __name__ == "__main__":
    main()
