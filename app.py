import pandas as pd
import plotly.graph_objects as go
from streamlit_embedcode import github_gist
from streamlit_ace import st_ace

import streamlit as st
import sqlite3

st.info('Meu objetivo com esse projeto é demonstrar meus conhecimentos de Python e SQL com um Front-end que eu mesmo '
        'desenvolvi com Streamlit 🙂👍 (De: Gustavo Lídio Damaceno)', icon="ℹ️")

tab1, tab2 = st.tabs(["main", "others"])

conn = sqlite3.connect('src/database.db')

with tab1:

    table_container, input_container, console_container = st.container(), st.container(), st.empty()

    with console_container:
        content = st_ace(language='sql')

    with input_container:
        table_name = st.text_input('Digite um nome para a tabela:')

        if st.button('Criar Tabela'):
            text = f"CREATE TABLE IF NOT EXISTS {table_name} (id INTEGER PRIMARY KEY, nome TEXT NOT NULL);"
            #conn.execute(
            #    f"CREATE TABLE IF NOT EXISTS {table_name} (id INTEGER PRIMARY KEY, nome TEXT NOT NULL);"
            #)

    with console_container:
        content = st_ace(language='sql', value=text)

    with table_container:
        cursor = conn.execute(f"SELECT id, nome from {table_name}")
        dados = [(linha[0], linha[1]) for linha in cursor]

        df = pd.DataFrame(dados)
        st.experimental_data_editor(df)


with tab2:
    st.write("em breve")

conn.close()
