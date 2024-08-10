import streamlit as st 
from utilities.calculations import get_weather_data
from database.db_manager import DatabaseManager
from database.operations import edit_entry, delete_entry
import logging
import sqlite3
import pandas as pd
logging.basicConfig(level=logging.DEBUG)


FILEPATH = r'data\temperature.txt'
DB_NAME = r'data\epi_stock.db'


def get_latest_data(db_manager):
    # Execute a consulta para obter todos os dados da tabela epi_stock
    data = db_manager.execute_query("SELECT * FROM epi_stock", fetch_all=True)
    
    # Crie um DataFrame com os dados e defina os nomes das colunas
    df = pd.DataFrame(data, columns=["ID", "EPI Name", "Quantity", "Transaction Type", "Date", "Value", "Requester", "CA"])
    
    # Defina a coluna 'ID' como o índice do DataFrame
    df.set_index("ID", inplace=True)
    
    return df


db_manager = DatabaseManager(DB_NAME)
df = get_latest_data(db_manager)

 

#----------------- Configurações de Página --------------------------------------
def set_page():
    st.set_page_config(
    page_title="Página Inicial", # Isso define o título da aba do navegador.
    page_icon="📋",  # Isso define um ícone para a aba (opcional).
    layout="wide",  # Isso define o layout da página.
    initial_sidebar_state="expanded"  # Isso expande a barra lateral por padrão.
)
#----------------------- Painel de métricas--------------------------------------
def temperatura_vento():
    # Tente recuperar os dados do clima
    try:
        data = get_weather_data(FILEPATH)
    except Exception as e:
        # Se ocorrer um erro, defina os dados como None ou algum valor padrão
        data = {
            'temperature': 'N/A',
            'wind': 'N/A',
            'humidity': 'N/A'
        }
        # (Opcional) Escreva uma mensagem de erro no Streamlit ou no log
        st.error(f"Erro ao recuperar os dados de clima: {e}")
        logging.error(f"Erro ao recuperar os dados de clima: {e}")

    # Agora, quando você tenta exibir os dados de clima na sua aplicação, eles mostrarão 'N/A' ou o que você definir como valor padrão.
    col1, col2, col3 = st.columns(3)
    col1.metric("Temperatura em São Paulo", f"{data['temperature']}°C", "1.2 °F")
    col2.metric("Velocidade do Vento", data['wind'], '-8%')
    col3.metric("Umidade", data['humidity'], '4%')
    
#-------------- Obtenha uma lista de todos os nomes de EPI para o menu suspenso (somente se "saída" estiver selecionado)--------------------------
def entrance_exit_edit_delete(): 
    df = get_latest_data(db_manager)
                

    all_entrance_epi_names = [name[0] for name in db_manager.execute_query("SELECT DISTINCT epi_name FROM epi_stock WHERE transaction_type = 'entrada'", fetch_all=True)]

    with st.expander("Clique para inserir, editar ou excluir"):  # Esconde todos os campos de saída ou entrada
        requester = None
        transaction_type = st.selectbox("Tipo de transação:", ["entrada", "saída"])

        if transaction_type == "entrada":
            epi_name = st.text_input("Nome do EPI:", "")
        elif transaction_type == "saída":
            if all_entrance_epi_names:
                epi_name = st.selectbox("Nome do EPI:", all_entrance_epi_names)
            else:
                st.write("Não há entradas registradas no banco de dados.")

        quantity = st.number_input("Quantidade:", min_value=0, step=1)
        value = st.number_input("Valor:", min_value=0.0, step=0.01) if transaction_type == "entrada" else None
        ca = st.text_input("CA:", "") if transaction_type == "entrada" else None
        if transaction_type == "saída":
            requester = st.text_input("Solicitante:", "")
            exit_date = st.date_input("Data da saída:")

        if st.button("Adicionar"):
            if epi_name and quantity:
                if transaction_type == "entrada":
                    db_manager.add_entry(epi_name, int(quantity), transaction_type, None, float(value), int(ca), requester)
                    st.success("EPI adicionado com sucesso!")
                elif transaction_type == "saída" and requester:
                    epi_id = db_manager.execute_query("SELECT id FROM epi_stock WHERE epi_name = ?", (epi_name,))[0]
                    db_manager.add_exit(epi_id, int(quantity), requester, exit_date)
                    st.success("Saída registrada com sucesso!")
                else:
                    st.warning("Por favor, preencha todos os campos.")
            else:
                st.warning("Por favor, preencha todos os campos.")

        # Edição
        all_ids = [entry[0] for entry in db_manager.execute_query("SELECT id FROM epi_stock", fetch_all=True)]
        selected_id = st.selectbox("Selecione a linha que será editada:", all_ids)

        if selected_id:
            st.session_state.id = str(selected_id)

        if st.session_state.get('id'):
            id = int(st.session_state.id)
            # Verifica se o ID está no DataFrame
            if id in df.index:
                selected_row = df.loc[id]
                epi_name = st.text_input("Nome do EPI:", value=selected_row["EPI Name"])
                quantity = st.number_input("Quantidade:", value=int(selected_row["Quantity"]))
                value = st.number_input("Valor:", value=float(selected_row["Value"]))
                transaction_type = st.text_input("Tipo de transação:", value=selected_row["Transaction Type"])

                if st.button("Editar"):
                    edit_entry(db_manager, id, epi_name, quantity, value, transaction_type)
                    st.success("EPI editado com sucesso!")
                    # Limpa os campos e o ID selecionado após a edição
                    if 'id' in st.session_state:
                        del st.session_state['id']
            else:
                st.warning("O ID selecionado não está disponível para edição.")

        # Exclusão
        all_epi_ids = [entry[0] for entry in db_manager.execute_query("SELECT id FROM epi_stock", fetch_all=True)]

        if all_epi_ids:
            selected_id = st.selectbox("Com Cautela! Selecione o ID da entrada ou saída para excluir:", all_epi_ids)
            if st.button("Excluir"):
                delete_entry(db_manager, selected_id)
                st.success(f"A entrada/saída com ID {selected_id} foi excluída com sucesso!")
        else:
            st.write("Não há entradas/saídas registradas no banco de dados.")



                            
            df = get_latest_data(db_manager)
                
#--------------------------------- Dropdown de Exclusão de ID ---------------------------------------------------------------
        
            all_epi_ids = [entry[0] for entry in db_manager.execute_query("SELECT id FROM epi_stock", fetch_all=True)]

            if all_epi_ids:
                selected_id = st.selectbox("Com Cautela! Selecione o ID da entrada ou saída para excluir:", all_epi_ids)
                if st.button("Excluir"):
                    delete_entry(db_manager, selected_id)
                    st.success(f"A entrada/saída com ID {selected_id} foi excluída com sucesso!")
            else:
                st.write("Não há entradas/saídas registradas no banco de dados.")                    

#---------------------------------- Dataframe principal ---------------------------------------------------------------

def frame_page_one():
    
    
    df = get_latest_data(db_manager)
    
    # Converter a coluna 'Date' para o formato datetime
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    
    st.dataframe(data=df,
                    column_config={'Value':st.column_config.NumberColumn(
                    "Valor",
                    help= "O preço do material em Reais",
                    min_value= 0,
                    max_value= 100000,
                    step= 1,
                    format= '$ %.2f'
                    ),
#------------------- Config da coluna Nome-------------------------------------------              
                    'EPI Name': st.column_config.TextColumn(
                    'Equipamento',
                    help= 'Nome do EPI',
                    default='st.',
                    max_chars=50,
                    
                    ),
#-------------------Coluna de Numero -----------------------
                    'Quantity': st.column_config.NumberColumn(
                    'Quantidade',
                    help= 'Quantidade de EPI',
                    min_value=0,
                    max_value=1000000,
                    step=1,
                    format='%.0f',     
                    ),
#--------------------Coluna de texto tipo de EPI --------------------                    
                    'Transaction Type': st.column_config.TextColumn(
                    'Transação',
                    help= 'Entrada ou Saída',
                    default='st.',
                    max_chars=50,
                    ),
                    'CA': st.column_config.NumberColumn(
                    'CA',
                    help= 'Certificado de Aprovação se aplicável',
                    min_value=0,
                    max_value=1000000,
                    step=1,
                    format='%.0f',     
                    ),
#-------------------Coluna de Data -----------------------------                    
                    'Date': st.column_config.DateColumn(
                    'Data',
                    help= 'Data da transação',
                    format='DD/MM/YYYY',
                    step=1,                 
                    ),
#-----------------------Coluna de Texto----------------------------------                    
                    'Requester': st.column_config.TextColumn(
                    'Requisitante',
                    help= 'Requisitante do Equipamento',
                    default='st.',
                    max_chars=50,
                    
                    ),
                                                                                                              
                                    }, hide_index=True,
        )                        
