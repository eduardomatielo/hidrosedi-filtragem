import os
import pandas as pd
import streamlit as st
from io import BytesIO
from PIL import Image

# Configuração de estilo CSS (Modern & Floating UI)
CUSTOM_CSS = """
<style>
    /* Fundo da tela principal (cinza bem claro para o contraste) */
    [data-testid="stAppViewContainer"] {
        background-color: #f4f7f9;
    }

    /* --- Efeito Flutuante na Barra Lateral --- */
    /* Deixa o container raiz transparente */
    [data-testid="stSidebar"] {
        background-color: transparent !important;
    }
    /* Cria o "card" branco flutuante dentro da barra */
    [data-testid="stSidebar"] > div:first-child {
        background-color: #ffffff;
        margin: 16px;
        border-radius: 20px;
        box-shadow: 0px 8px 24px rgba(0, 0, 0, 0.08);
        height: calc(100vh - 32px); /* Altura total menos a margem */
    }

    /* Textos da barra lateral */
    [data-testid="stSidebar"] * {
        color: #334155;
    }

    /* --- Botões Modernos (com gradiente e sombra) --- */
    .stButton>button {
        background: linear-gradient(135deg, #57a4a5 0%, #3e8283 100%);
        color: white;
        border: none;
        border-radius: 12px;
        font-weight: 600;
        padding: 8px 16px;
        box-shadow: 0 4px 12px rgba(87, 164, 165, 0.25);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px); /* Efeito de pular ao passar o mouse */
        box-shadow: 0 6px 16px rgba(87, 164, 165, 0.4);
        color: white;
    }

    /* --- Caixa de Upload (File Uploader) --- */
    [data-testid="stFileUploader"] {
        background-color: #ffffff;
        border: 2px dashed #cbd5e1;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.03);
        transition: all 0.3s ease;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #57a4a5;
        background-color: #fcfefe;
    }

    /* Títulos e textos principais */
    h1, h2, h3 {
        color: #1e293b;
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }
    p, span, label {
        color: #475569;
    }
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
                
                # --- CORREÇÃO: Ignorar dados de quando o relógio do datalogger desregulou ---
            df = df[df['Data'].dt.year > 2010]
                
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


