# Imports
import pandas            as pd
import streamlit         as st
import seaborn           as sns
import matplotlib.pyplot as plt
from PIL                import Image
from io                 import BytesIO
import os

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

    dir_path = os.path.dirname(__file__)
image_path = os.path.join(dir_path, "Bank-Branding.jpg")

try:
    image = Image.open(image_path)
    st.sidebar.image(image)
except FileNotFoundError:
    st.sidebar.warning(f"Imagem '{image_path}' não encontrada.")

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
            default_selected = st.multiselect("Default", options_with_all('default'), ['all'])
            housing_selected = st.multiselect("Financiamento imobiliário", options_with_all('housing'), ['all'])
            loan_selected = st.multiselect("Empréstimo", options_with_all('loan'), ['all'])
            contact_selected = st.multiselect("Meio de contato", options_with_all('contact'), ['all'])
            month_selected = st.multiselect("Mês do contato", options_with_all('month'), ['all'])
            day_of_week_selected = st.multiselect("Dia da semana", options_with_all('day_of_week'), ['all'])

            submit_button = st.form_submit_button('Aplicar')

        if submit_button:
            # Aplicar filtros
            bank = (
                bank.query("age >= @idades[0] and age <= @idades[1]")
                    .pipe(multiselect_filter, 'job', jobs_selected)
                    .pipe(multiselect_filter, 'marital', marital_selected)
                    .pipe(multiselect_filter, 'default', default_selected)
                    .pipe(multiselect_filter, 'housing', housing_selected)
                    .pipe(multiselect_filter, 'loan', loan_selected)
                    .pipe(multiselect_filter, 'contact', contact_selected)
                    .pipe(multiselect_filter, 'month', month_selected)
                    .pipe(multiselect_filter, 'day_of_week', day_of_week_selected)
            )

            st.subheader('Dados após filtros')
            st.dataframe(bank.head())

            # Botão para download Excel
            df_xlsx = to_excel(bank)
            st.download_button(
                label='📥 Baixar dados filtrados em Excel',
                data=df_xlsx,
                file_name='bank_filtered.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )

            st.markdown("---")

            # Gráficos proporção de "y"
            fig, ax = plt.subplots(1, 2, figsize=(10, 4))

            bank_raw_target_perc = bank_raw['y'].value_counts(normalize=True).sort_index() * 100
            bank_target_perc = bank['y'].value_counts(normalize=True).sort_index() * 100

            # Mostrar tabelas e download dos dados
            col1, col2 = st.columns(2)

            col1.subheader('Proporção original')
            col1.dataframe(bank_raw_target_perc.to_frame(name='Percentual (%)'))
            col1.download_button(
                label='📥 Download original',
                data=convert_df(bank_raw_target_perc.to_frame()),
                file_name='bank_raw_y.csv',
                mime='text/csv'
            )

            col2.subheader('Proporção após filtro')
            col2.dataframe(bank_target_perc.to_frame(name='Percentual (%)'))
            col2.download_button(
                label='📥 Download filtrado',
                data=convert_df(bank_target_perc.to_frame()),
                file_name='bank_filtered_y.csv',
                mime='text/csv'
            )

            st.markdown("---")

            st.subheader('Proporção de aceite')

            if graph_type == 'Barras':
                sns.barplot(x=bank_raw_target_perc.index, y=bank_raw_target_perc.values, ax=ax[0])
                ax[0].bar_label(ax[0].containers[0])
                ax[0].set_title('Dados brutos', fontweight="bold")

                sns.barplot(x=bank_target_perc.index, y=bank_target_perc.values, ax=ax[1])
                ax[1].bar_label(ax[1].containers[0])
                ax[1].set_title('Dados filtrados', fontweight="bold")
            else:
                bank_raw_target_perc.plot(kind='pie', autopct='%.2f%%', ax=ax[0])
                ax[0].set_ylabel('')
                ax[0].set_title('Dados brutos', fontweight="bold")

                bank_target_perc.plot(kind='pie', autopct='%.2f%%', ax=ax[1])
                ax[1].set_ylabel('')
                ax[1].set_title('Dados filtrados', fontweight="bold")

            st.pyplot(fig)

        else:
            st.info("Use o formulário lateral para aplicar filtros.")

    else:
        st.info("⬆️ Por favor, envie um arquivo `.csv` ou `.xlsx` para iniciar a análise.")


if __name__ == '__main__':
    main()









