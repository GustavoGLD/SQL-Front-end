import sqlite3
from typing import List, Tuple
import ast
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit.delta_generator import DeltaGenerator
from streamlit_ace import st_ace
from streamlit_embedcode import github_gist
from typing import Optional, Union, Any


class Code:
    create_table = '''    
    def create_table(self, table_name: str, columns: List[Tuple[str, str]]):
        """
        Cria uma tabela no banco de dados SQLite.

        Args:
        - table_name: str - o nome da tabela a ser criada.
        - columns: List[Tuple[str, str]] - uma lista de tuplas contendo o nome e o tipo de dados de cada coluna.

        Returns:
        - None
        """

        # Converte as tuplas em strings formatadas de coluna e tipo de dados usando a função join().
        column_defs = ", ".join([f"{name} {_type}" for name, _type in columns])
        
        # Define uma string de consulta SQL para criar a tabela com a sintaxe CREATE TABLE.
        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({column_defs})"
        
        # Executa a consulta na conexão do banco de dados usando o método execute().
        self.conn.execute(query)
    '''

    insert_data = '''
        def insert_data(self, table_name: str, data: List[Tuple]):
            """
            Insere dados em uma tabela no banco de dados SQLite.
    
            Args:
            - table_name: str - o nome da tabela na qual os dados serão inseridos.
            - data: List[Tuple] - uma lista de tuplas contendo os valores a serem inseridos em cada coluna.
    
            Returns:
            - None
            """
    
            # Cria uma string de marcadores de posição para as colunas usando a função join().
            placeholders = ", ".join(["?" for _ in range(len(data[0]))])
            
            # Define uma string de consulta SQL para inserir dados na tabela com a sintaxe INSERT INTO.
            query = f"INSERT INTO {table_name} VALUES ({placeholders})"
            
            # Executa a consulta na conexão do banco de dados usando o método executemany().
            self.conn.executemany(query, data)
        '''

    get_data = '''
        def get_data_frame(self, table_name: str) -> pd.DataFrame:
            """
            Retorna os dados da tabela especificada em um pandas DataFrame.
        
            Parâmetros:
                table_name (str): nome da tabela a ser consultada.
        
            Retorno:
                pd.DataFrame: DataFrame contendo as informações da tabela.
            """
            # Executa a query para obter todos os dados da tabela
            data_array = self.conn.execute(f"SELECT * from {table_name}").fetchall()
        
            # Executa a query para obter as informações das colunas da tabela
            data_info = self.conn.execute(f"PRAGMA table_info({table_name});").fetchall()
        
            # Extrai os nomes das colunas e armazena em uma lista
            columns_names = [column[1] for column in data_info]
        
            # Cria um DataFrame a partir da lista de tuplas
            df = pd.DataFrame(data_array, columns=columns_names)
        
            return df
        '''


class DatabaseManager:
    def __init__(self, db_name: str):
        self.conn = sqlite3.connect(db_name)
        self.__table_names: list[str] = []
        self.__log_container: Optional[DeltaGenerator] = None
        self.__log = ""

    @property
    def table_names(self) -> list[str]:
        return self.__table_names

    def config_log(self, empty_container: DeltaGenerator):
        self.__log_container = empty_container

    def _append_to_log(self, txt: Union[str, Any], output: bool = False):
        self.__log += f'\n-- OUTPUT: {str(txt)}' if output else f'\n{str(txt)}'
        if self.__log_container:
            self.__log_container.code(self.__log, language='sql')
            print("--LOG--", self.__log)

    def create_table(self, table_name: str, columns: List[Tuple[str, str]]):
        column_defs = ", ".join([f"{name} {_type}" for name, _type in columns])
        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({column_defs});"
        self.conn.execute(query)
        self.__table_names.append(table_name)
        self._append_to_log(query)

    def insert_data(self, table_name: str, data: List[Tuple]):
        values_sql = ', '.join(["('{}', {})".format(*row) for row in data])
        query = f"INSERT INTO {table_name} VALUES {values_sql};"

        self.conn.execute(query)
        self._append_to_log(query)

    def get_data(self, table_name: str):
        select_query = f"SELECT * from {table_name};"
        pragma_query = f"PRAGMA table_info({table_name});"

        data_array = self.conn.execute(select_query).fetchall()
        data_info = self.conn.execute(pragma_query).fetchall()

        self._append_to_log(select_query)
        self._append_to_log(data_array, output=True)
        # self._append_to_log(pragma_query)
        # self._append_to_log(f'-- {str(data_info)}')

        columns = [d[1] for d in data_info]
        return pd.DataFrame(data_array, columns=columns)

    def close(self):
        self.conn.close()


def main():
    st.info(
        'Meu objetivo com esse projeto é demonstrar meus conhecimentos de Python e SQL com um Front-end que eu mesmo '
        'desenvolvi com Streamlit 🙂👍 (De: Gustavo Lídio Damaceno)', icon="ℹ️")

    db_manager = DatabaseManager('src/database.db')
    session_state = st.session_state

    tab1, tab2 = st.tabs(["Main", "Código Fonte / Info"])

    with tab1:
        main_tab(session_state, db_manager)

    with tab2:
        with st.expander('Criando uma tabela'):
            st.code(Code.create_table, language='python')
        with st.expander('Inserindo dados'):
            st.code(Code.insert_data, language='python')
        with st.expander('Obtendo dados'):
            st.code(Code.get_data, language='python')

    db_manager.close()


def main_tab(session_state, db_manager: DatabaseManager):
    table_container, input_container, log_container = st.container(), st.container(), st.empty()

    db_manager.config_log(log_container)

    with input_container:
        if table_name := st.text_input('Digite um nome para a tabela:'):
            processing_input(db_manager, table_name)

    with table_container:
        st.write(db_manager.table_names)
        if table_name := st.text_input(
                'Digite o nome da tabela para visualizar os dados:'
        ):
            data = db_manager.get_data(table_name)
            if not data.empty:
                st.write(data)
            else:
                st.write(f"Nenhum dado encontrado na tabela {table_name}")


def processing_input(db_manager: DatabaseManager, table_name):
    if columns := st.text_input('Digite os nomes e tipos de dados das colunas (ex.: nome TEXT, idade INTEGER):',
                                placeholder='nome TEXT, idade INTEGER'):
        columns = [tuple(c.strip().split()) for c in columns.split(",")]
        db_manager.create_table(table_name, columns)

        if data_str := st.text_input('Digite os dados a serem inseridos na tabela (ex.: ("João", 25), ("Maria", 30)):',
                                     placeholder='("João", 25), ("Maria", 30)'):
            data = ast.literal_eval(f"[{data_str}]")
            db_manager.insert_data(table_name, data)


if __name__ == '__main__':
    main()
