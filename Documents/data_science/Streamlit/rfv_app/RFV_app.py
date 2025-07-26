import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="Segmentação RFV", layout="wide")

st.title("📊 Segmentação de Clientes - RFV")

st.markdown(
    """
    Este app realiza a análise de segmentação de clientes com base no modelo **RFV (Recência, Frequência, Valor)**.

    Faça upload de um arquivo `.csv` contendo os dados de compras com as colunas obrigatórias:
    - `ID_cliente`
    - `CodigoCompra`
    - `ValorTotal`
    - `DiaCompra`
    """
)

# Upload
uploaded_file = st.file_uploader("📁 Upload do arquivo CSV de compras", type="csv")

if uploaded_file:
    @st.cache_data
    def carregar_dados(file):
        return pd.read_csv(file, parse_dates=['DiaCompra'])

    df_compras = carregar_dados(uploaded_file)

    # Validação de colunas
    colunas_esperadas = {'ID_cliente', 'CodigoCompra', 'ValorTotal', 'DiaCompra'}
    if not colunas_esperadas.issubset(df_compras.columns):
        st.error("❌ O arquivo deve conter as colunas: ID_cliente, CodigoCompra, ValorTotal e DiaCompra.")
        st.stop()

    # Validação leve da coluna de data
    if not pd.api.types.is_datetime64_any_dtype(df_compras['DiaCompra']):
        st.error("❌ A coluna 'DiaCompra' não foi interpretada como data.")
        st.stop()

    dia_atual = datetime(2021, 12, 9)

    # Recência
    df_recencia = df_compras.groupby('ID_cliente')['DiaCompra'].max().reset_index()
    df_recencia['Recencia'] = (dia_atual - df_recencia['DiaCompra']).dt.days

    # Frequência
    df_frequencia = df_compras.groupby('ID_cliente')['CodigoCompra'].count().reset_index()
    df_frequencia.columns = ['ID_cliente', 'Frequencia']

    # Valor
    df_valor = df_compras.groupby('ID_cliente')['ValorTotal'].sum().reset_index()
    df_valor.columns = ['ID_cliente', 'Valor']

    # União dos dados
    df = df_recencia.merge(df_frequencia, on='ID_cliente').merge(df_valor, on='ID_cliente')
    df.set_index('ID_cliente', inplace=True)

    # Quartis
    q = df.quantile(q=[0.25, 0.5, 0.75]).to_dict()

    def recencia_class(x):
        if x <= q['Recencia'][0.25]:
            return 'A'
        elif x <= q['Recencia'][0.50]:
            return 'B'
        elif x <= q['Recencia'][0.75]:
            return 'C'
        else:
            return 'D'

    def freq_val_class(x, col):
        if x <= q[col][0.25]:
            return 'D'
        elif x <= q[col][0.50]:
            return 'C'
        elif x <= q[col][0.75]:
            return 'B'
        else:
            return 'A'

    # Cálculo das notas
    df['R_quartil'] = df['Recencia'].apply(recencia_class)
    df['F_quartil'] = df['Frequencia'].apply(lambda x: freq_val_class(x, 'Frequencia'))
    df['V_quartil'] = df['Valor'].apply(lambda x: freq_val_class(x, 'Valor'))
    df['RFV_Score'] = df['R_quartil'] + df['F_quartil'] + df['V_quartil']

    # Ações sugeridas
    acoes = {
        'AAA': 'Enviar cupons de desconto, pedir indicação e enviar amostras grátis.',
        'DDD': 'Churn provável. Fazer nada.',
        'DAA': 'Churn possível. Tentar recuperar com cupons.',
        'CAA': 'Churn possível. Tentar recuperar com cupons.'
    }
    df['Ação de Marketing'] = df['RFV_Score'].map(acoes)

    # Mostra tabela
    st.subheader("📌 Top 10 clientes com maior valor total")
    df_exibicao = df.sort_values('Valor', ascending=False).head(10).copy()
    df_exibicao['Valor'] = df_exibicao['Valor'].apply(lambda x: f"R$ {x:,.2f}")
    st.dataframe(df_exibicao)

    # Exportação
    df_excel = df.reset_index()
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_excel.to_excel(writer, index=False, sheet_name='RFV')

    st.download_button(
        label="📂 Baixar resultado em Excel",
        data=buffer.getvalue(),
        file_name="Segmentacao_RFV.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.success("✅ Análise concluída com sucesso!")

else:
    st.info("⬆️ Por favor, envie um arquivo `.csv` para iniciar a análise.")

