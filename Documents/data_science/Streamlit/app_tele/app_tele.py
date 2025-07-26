# Imports
import pandas            as pd
import streamlit         as st
import seaborn           as sns
import matplotlib.pyplot as plt
from PIL                import Image
from io                 import BytesIO

# Configuração do tema do seaborn
custom_params = {"axes.spines.right": False, "axes.spines.top": False}
sns.set_theme(style="ticks", rc=custom_params)


# Função para ler os dados, com cache atualizado
@st.cache_data(show_spinner=True)
def load_data(file_data):
    try:
        return pd.read_csv(file_data, sep=';')
    except Exception:
        return pd.read_excel(file_data)


# Função para filtrar baseado na multiseleção de categorias
@st.cache_data
def multiselect_filter(relatorio, col, selecionados):
    if 'all' in selecionados:
        return relatorio
    else:
        return relatorio[relatorio[col].isin(selecionados)].reset_index(drop=True)


# Função para converter o df para csv
@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')


# Função para converter o df para excel
@st.cache_data
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    processed_data = output.getvalue()
    return processed_data


# Função principal da aplicação
def main():
    # Configuração da página
    st.set_page_config(
        page_title='Telemarketing Analysis',
        page_icon='📞',
        layout="wide",
        initial_sidebar_state='expanded'
    )

    # Título principal
    st.title('📞 Telemarketing Analysis')
    st.markdown("---")

    # Imagem lateral
    try:
        image = Image.open("Bank-Branding.jpg")
        st.sidebar.image(image)
    except FileNotFoundError:
        st.sidebar.warning("Imagem 'Bank-Branding.jpg' não encontrada.")

    # Upload do arquivo
    st.sidebar.header("📁 Faça upload do arquivo")
    data_file = st.sidebar.file_uploader("Bank marketing data (CSV ou XLSX)", type=['csv', 'xlsx'])

    if data_file is not None:
        bank_raw = load_data(data_file)
        bank = bank_raw.copy()

        st.subheader('Dados originais (antes dos filtros)')
        st.dataframe(bank_raw.head())

        # Filtros no sidebar com formulário
        with st.sidebar.form(key='filters_form'):
            graph_type = st.radio('Tipo de gráfico:', ('Barras', 'Pizza'))

            # Faixa de idade
            min_age, max_age = int(bank.age.min()), int(bank.age.max())
            idades = st.slider('Idade', min_value=min_age, max_value=max_age, value=(min_age, max_age), step=1)

            # Função para criar lista de opções + 'all'
            def options_with_all(col):
                opts = bank[col].dropna().unique().tolist()
                if 'all' not in opts:
                    opts.append('all')
                return opts

            jobs_selected = st.multiselect("Profissão", options_with_all('job'), ['all'])
            marital_selected = st.multiselect("Estado civil", options_with_all('marital'), ['all'])
            default_selected = st.multiselect("Default", options_with_all('default')_

    









