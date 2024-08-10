import os
import json
import streamlit as st
from configs.config_front import set_page, temperatura_vento, entrance_exit_edit_delete, frame_page_one
from database.db_manager import DatabaseManager
from database.operations import display_image_data, front_pdf_generate, get_closest_match_name
from utilities.excel_importer import import_from_excel
import pandas as pd
from configs.config_front_page2 import forecast_fromhere, front_inventario
from utilities.calculations import calculate_forecast, save_forecast_to_json, retrieve_forecast_from_json, get_forecast_data, show_progress_bar
from utilities.insights import generate_uniform_pairs_insight, display_monthly_insights
from logins.login import load_users_db, log_attempt, login, logout
import logging
import datetime
from logins.adm_interface import admin_interface

logging.basicConfig(level=logging.DEBUG)

#---------------------------------- Dados ------------------------------------------------
FILEPATH = r'data\temperature.txt'
DB_NAME = r'data\epi_stock.db'
JSON_PATH = r'data\data.json'
USERS_DB_PATH = r'data\users_db.json'

#--------------------------- Nome da Página e Configurações ------------------------------
set_page()

#------------------ Temperatura, Velocidade do vento, Umidade -----------------------------
temperatura_vento()

#------------------------ Configurações --------------------------------
def get_latest_data(db_manager):
    data = db_manager.execute_query("SELECT * FROM epi_stock", fetch_all=True)
    return pd.DataFrame(data, columns=["ID", "EPI Name", "Quantity", "Transaction Type", "Date", "Value", "Requester", "CA"])

#--------------------------- Classe Main --------------------------------
def main(): 
    # Carregar o banco de dados de usuários
    users_db = load_users_db()

    # Verificar se o usuário está logado
    if not st.session_state.get('logged_in', False):
        # Se o usuário não estiver logado, mostrar a tela de login
        login(users_db)
        return  # Retornar aqui para garantir que nada mais é exibido até o login ser bem-sucedido
    
    # Código para quando o usuário estiver logado
    st.sidebar.button("Logout", on_click=logout)  # Adicionar o botão de logout na barra lateral

    progress_placeholder = st.empty()
    show_progress_bar(progress_placeholder)
    progress_placeholder.empty()

    db_manager = DatabaseManager(DB_NAME)
    df = get_latest_data(db_manager)
    
    if not os.path.isfile(DB_NAME):
        db_manager.create_table()

    page = st.sidebar.selectbox("Escolha a página:", ["Página Inicial", "Custo", "Inventário", "Administração"])
    
    if page == "Página Inicial":  # Página inicial da aplicação
        st.title("Gerenciamento de Equipamentos de Proteção Individual")
        st.caption('EPI Stock Management')
        st.subheader("Adicione Entradas e Saídas")

        # Exibir nome do usuário logado
        username = st.session_state.get('username')
        if username:
            user_name = users_db.get(username, {}).get('name', 'Usuário')
            st.sidebar.write(f"Bem-vindo, {user_name}!")

        # Criar a tabela budget_forecast se ela não existir
        db_manager.create_budget_forecast_table()
        
        # Interface da barra lateral para definir a previsão orçamentária
        st.sidebar.subheader("Orçamento Fechado")
        year = st.sidebar.number_input("Ano:", min_value=2023, step=1)
        forecast = st.sidebar.number_input("Previsão Orçamentária:", min_value=0.0, step=0.01)
        if st.sidebar.button("Definir Previsão"):
            db_manager.set_budget_forecast(year, forecast)
            st.success('O orçamento foi definido')
        
        # Obtenha uma lista de todos os nomes de EPI para o menu suspenso (somente se "saída" estiver selecionado adicione edite e exclua)
        entrance_exit_edit_delete()          
        
        # Display the dataframe
        frame_page_one()                     
        
        # Calcular o total para cada EPI (entradas - saídas)
        unique_epi_names = df['EPI Name'].unique()
        name_mapping = {name: get_closest_match_name(name, unique_epi_names) for name in unique_epi_names}
        df['EPI Name'] = df['EPI Name'].map(name_mapping)
        total_epi = df.groupby('EPI Name')['Quantity'].sum().sort_values()
        entradas_df = df[df['Transaction Type'] == 'entrada'].copy()  # Use .copy() to avoid SettingWithCopyWarning
        epis_at_zero = total_epi[total_epi == 0].index.tolist()

        # Exibir a barra de progresso referente ao orçamento fechado x o gasto
        current_year = datetime.datetime.now().year
        selected_year = st.session_state.get("selected_year", current_year)
        if st.button("Reiniciar Barra de Progresso"):
            selected_year = current_year
        selected_year = st.selectbox("Escolha o ano:", range(current_year - 5, current_year + 1), index=selected_year - (current_year - 5))
        st.session_state.selected_year = selected_year

        # Garantir que 'Date' é convertida corretamente para datetime
        entradas_df['Date'] = pd.to_datetime(entradas_df['Date'], errors='coerce')
        if entradas_df['Date'].notnull().any():
            selected_year_trans = entradas_df[entradas_df['Date'].dt.year == selected_year]
        else:
            selected_year_trans = pd.DataFrame()  # DataFrame vazio para evitar erros

        forecast = db_manager.get_budget_forecast(selected_year)
        if forecast:
            total_entradas_value = (selected_year_trans['Quantity'] * selected_year_trans['Value']).sum()
            progress = total_entradas_value / forecast
            progress = min(1.0, progress)
            st.subheader('Posição atual do custo previsto')
            st.progress(progress)
            st.text(f"Valor total: ${forecast:.2f}, Valor gasto: ${total_entradas_value:.2f}")

        # Plotar o gráfico de barras
        st.subheader('Demonstrativo da posição do estoque atual')
        st.bar_chart(total_epi)

        # Se houver algum EPI com total zero, mostre um alerta no Streamlit
        unique_epi_names = df['EPI Name'].unique()
        df['Matched EPI Name'] = df['EPI Name'].apply(lambda x: get_closest_match_name(x, unique_epi_names))
        total_epi = df.groupby('Matched EPI Name')['Quantity'].sum()
        epis_at_stocklow = total_epi[total_epi <= 1].index.difference(epis_at_zero).tolist()
        if epis_at_stocklow:
            st.warning(f"Alerta! Avalie a reposição do estoque de: {', '.join(epis_at_stocklow)}")




        # Interface da barra lateral para importação do Excel
        st.sidebar.subheader("Importe dados do Excel")
        uploaded_file = st.sidebar.file_uploader("Escolha um arquivo Excel", type=["xlsx", "xls"])
        if uploaded_file:
            if st.sidebar.button("Importar Excel"):
                import_from_excel(db_manager, uploaded_file)   

        # Insights da Página Inicial
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')  # Repetir para garantir que 'Date' esteja no formato correto
        display_monthly_insights(df)

    elif page == "Custo":
        # Edição de Previsão de Aquisição
        forecast_fromhere()
        
        # Gerador de PDF
        front_pdf_generate()               

        # Interface da barra lateral para definir a previsão orçamentária
        st.sidebar.subheader("Previsão de Gastos para o Ano")
        year = st.sidebar.number_input("Ano:", min_value=2023, step=1, key="unique_key_for_year_input")
        if st.sidebar.button("Calcular Previsão"):
            forecast = calculate_forecast(JSON_PATH)
            save_forecast_to_json(year, forecast)
        forecast_value = retrieve_forecast_from_json(year)
        if forecast_value:
            st.sidebar.write(f"Previsão de Gastos para {year}: ${forecast_value:.2f}")       
        
        # Gráfico Barras total por tipo
        st.title("Previsão de Gastos para o ano seguinte")
        st.text("Consolidado por tipo")

        data_dict = get_forecast_data(JSON_PATH)
        data_in_reais = {key: f"R$ {value:,.2f}" for key, value in data_dict.items()}
        for tipo, valor in data_in_reais.items():
            st.write(f"{tipo}: {valor}")
        st.bar_chart(data_dict)

        # Insights
        generate_uniform_pairs_insight(JSON_PATH)

    elif page == "Inventário":
        front_inventario()
        st.write('Demonstrativo de equipamentos no contrato, (Em atualização).')
        display_image_data()

    elif page == "Administração":
        admin_interface()  # Chama a interface administrativa

# Execução do APP
if __name__ == "__main__":
    main()
    st.caption('Desenvolvido por Cristian Ferreira Carlos')

