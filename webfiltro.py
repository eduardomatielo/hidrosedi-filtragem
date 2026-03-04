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
    #st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

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
    
    # Adicionado suporte a separadores comuns em .dat
    sep_map = {"Ponto e vírgula (;)" : ";", "Tabulação (\\t)": "\t", "Vírgula (,)": ",", "Espaço": " "}
    sep_label = st.sidebar.selectbox("Separador do Arquivo", options=list(sep_map.keys()))
    delimiter = sep_map[sep_label]

    mode = st.sidebar.radio(
        "Método:",
        ("Horas Exatas (00 min)", "Regularização (Nearest)")
    )
    
    st.sidebar.markdown("---")
    st.sidebar.info("Suporte: .csv, .dat, .txt")

    # Main App
    st.write("")
    st.markdown("### Carregue seu arquivo")
    
    # Atualizado para aceitar .dat e .txt
    uploaded = st.file_uploader("Arquivo de dados", type=['csv', 'dat', 'txt'])

    if uploaded:
        st.markdown("### Resultado")
        try:
            # Load Data com o separador selecionado
            df = pd.read_csv(uploaded, sep=delimiter, dayfirst=True)
            
            # Pegamos todas as colunas do arquivo
            colunas_disponiveis = df.columns.tolist()
            
            # Tenta adivinhar qual é a coluna de data para facilitar a vida do usuário
            sugestao_index = 0
            for i, col in enumerate(colunas_disponiveis):
                nome_limpo = str(col).strip().lower()
                if nome_limpo in ['data', 'date', 'datahora', 'data_hora', 'timestamp', 'tempo', 't']:
                    sugestao_index = i
                    break

            # Cria um selectbox para o usuário confirmar ou escolher a coluna correta
            coluna_selecionada = st.selectbox(
                "Qual coluna contém as Datas e Horas?", 
                options=colunas_disponiveis,
                index=sugestao_index
            )

            # Renomeia a coluna escolhida para 'Data' para manter a compatibilidade com o resto do seu código
            df = df.rename(columns={coluna_selecionada: 'Data'})

            # Datetime conversion
            try:
                df['Data'] = pd.to_datetime(df['Data'], dayfirst=True)
            except ValueError:
                # Fallback format caso o automático falhe
                df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y %H:%M', errors='coerce')
            
            # Remove linhas onde a conversão de data falhou (NaT)
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

            # Formatting
            res['Data'] = res['Data'].dt.strftime('%d/%m/%Y %H:%M')

            # Output
            st.success(f"Processado: {len(res)} registros.")
            st.dataframe(res.head(), use_container_width=True)

            st.download_button(
                label="📥 Baixar Excel (.xlsx)",
                data=get_excel_buffer(res),
                file_name="hidrosedi_filtrado.xlsx",
                mime="application/vnd.ms-excel"
            )

        except Exception as e:
            st.error(f"Erro de Leitura: {e}")
            st.info("Dica: Verifique se o separador correto foi escolhido na barra lateral.")

