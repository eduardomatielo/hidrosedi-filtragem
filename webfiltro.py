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
    st.sidebar.info("A inteligência de filtragem agora é 100% automática!\n\n**Reconhecimento:**\n- Formato Padrão ou Datalogger TOA5\n- Separador fixo: Vírgula (,)\n- Horários Exatos ou Quebrados\n- Conversão automática de dados vazios (NAN)")

    # Main App
    st.write("")
    st.markdown("### Carregue o seu ficheiro")
    
    uploaded = st.file_uploader("Ficheiro de dados", type=['csv', 'dat', 'txt'])

    if uploaded:
        st.markdown("---")
        try:
            # 1. Separador fixo como vírgula
            delimiter = ','
            
            # Ler a primeira linha para detetar se é um ficheiro de datalogger (TOA5)
            primeira_linha = uploaded.readline().decode('utf-8', errors='ignore')
            uploaded.seek(0) 
            
            # 2. Carregar os dados com a estrutura correta
            if "TOA5" in primeira_linha:
                df = pd.read_csv(uploaded, sep=delimiter, header=1, skiprows=[2, 3])
            else:
                df = pd.read_csv(uploaded, sep=delimiter)
            
            # 3. Forçar a primeira coluna a ser 'Data'
            primeira_coluna = df.columns[0]
            df = df.rename(columns={primeira_coluna: 'Data'})

            # --- CORREÇÃO 1: FORÇAR NÚMEROS E LIMPAR O TEXTO "NAN" ---
            colunas_sensores = df.columns.drop('Data')
            df[colunas_sensores] = df[colunas_sensores].apply(pd.to_numeric, errors='coerce')

            # Pré-visualização opcional dos dados crus (antes de filtrar)
            with st.expander("👀 Ver ficheiro original sem formatação"):
                st.dataframe(df.head(15), use_container_width=True)

            # 4. Conversão para Datetime flexível
            df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
            
            # Remove linhas que não puderam ser convertidas em data
            df = df.dropna(subset=['Data'])
            
            if df.empty:
                st.error("Erro: Nenhuma data válida encontrada no ficheiro. Verifique o formato.")
                st.stop()
                
            df = df.sort_values('Data')

            # 5. Inteligência Única de Filtragem (Grelha de Tempo)
            grid = pd.date_range(
                start=df['Data'].min().floor('h'),
                end=df['Data'].max().ceil('h'),
                freq='h'
            )
            
            res = pd.merge_asof(
                pd.DataFrame({'Data': grid}), 
                df, 
                on='Data', 
                direction='nearest',
                tolerance=pd.Timedelta('30min')
            )
            
            # --- CORREÇÃO 2: Apagar apenas se a linha estiver completamente vazia de dados ---
            if 'RECORD' in res.columns:
                res = res.dropna(subset=['RECORD'])
            else:
                # Fallback de segurança para ficheiros normais sem a coluna RECORD
                res = res.dropna(how='all', subset=colunas_sensores)

            # 6. Formatação Final
            res['Data'] = res['Data'].dt.strftime('%d/%m/%Y %H:%M')

            # Output
            st.success(f"Filtragem concluída automaticamente! Total de registos: {len(res)}")
            
            st.markdown("#### Pré-visualização da Planilha Filtrada")
            st.dataframe(res, use_container_width=True, height=350) 

            st.download_button(
                label="📥 Baixar Excel (.xlsx)",
                data=get_excel_buffer(res),
                file_name="hidrosedi_filtrado.xlsx",
                mime="application/vnd.ms-excel"
            )

        except Exception as e:
            st.error(f"Erro de Processamento: {e}")
            st.info("Dica: Verifique se o ficheiro não está corrompido ou se possui formatações fora do padrão.")

if __name__ == "__main__":
    main()
