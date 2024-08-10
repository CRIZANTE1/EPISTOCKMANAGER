import os
import json
import streamlit as st
from configs.config_front import set_page, temperatura_vento, entrance_exit_edit_delete,frame_page_one
from database.db_manager import DatabaseManager
from database.operations import display_image_data, generate_pdf_report_buffer, get_closest_match_name
from utilities.excel_importer import import_from_excel
import pandas as pd
from utilities.calculations import calculate_forecast, save_forecast_to_json, retrieve_forecast_from_json, get_forecast_data,  show_progress_bar, load_json, save_json, add_to_json
from utilities.insights import generate_uniform_pairs_insight, display_monthly_insights

import logging
logging.basicConfig(level=logging.DEBUG)




#----------------------------------Dados------------------------------------------------
FILEPATH = r'data\temperature.txt'
DB_NAME = r'data\epi_stock.db'
JSON_PATH = r'data\data.json'


#------------------------ Configurações --------------------------------
def get_latest_data(db_manager):
    data = db_manager.execute_query("SELECT * FROM epi_stock", fetch_all=True)
    return pd.DataFrame(data, columns=["ID","EPI Name", "Quantity", "Transaction Type", "Date", "Value", "Requester", "CA"])


#------------------------------------------Edição de Previsão de Aquisição -----------------------------------------------       
def forecast_fromhere():

        st.text ("Adicionar novo equipamento na previsão")

    # Seção para adicionar novas entradas
        with st.expander("Adicionar nova entrada"):
            epi_name = st.text_input("Nome do EPI:")
            quantity = st.number_input("Quantidade:", min_value=0)
            epi_type = st.text_input("Tipo:")
            value = st.number_input("Valor:", min_value=0.0)
            ca = st.number_input("CA:", min_value=0.0)
            
            if st.button("Adicionar"): 
                new_entry = {
                    "epi_name": epi_name,
                    "quantity": quantity,
                    "type": epi_type,
                    "value": value,
                    "CA": ca
                }
                add_to_json(new_entry)
                st.success("Registrado com sucesso!")
                
            

        # Carregar e editar os dados do JSON
        data = load_json()
        st.text("Editar a Previsão de Aquisição para o próximo ano")
        
#---------------------Data frame com permissão de edição -------------------------------        
        edited_data = st.data_editor(data, 
                    column_config={'value':st.column_config.NumberColumn(
                    "Valor",
                    help= "O preço do material em Reais",
                    min_value= 0,
                    max_value= 100000,
                    step= 1,
                    format= '$ %.2f'
                    ),
#------------------- Config da coluna Nome-------------------------------------------              
                    'epi_name': st.column_config.TextColumn(
                    'Equipamento',
                    help= 'Nome do EPI, Uniforme, Serviço',
                    default='st.',
                    max_chars=50,
                    
                    ),
#-------------------Coluna de Numero -----------------------
                    'quantity': st.column_config.NumberColumn(
                    'Quantidade',
                    help= 'Pode ser Equipamento ou Serviço',
                    min_value=0,
                    max_value=1000000,
                    step=1,
                    format='%.0f',     
                    ),
#--------------------Coluna de texto tipo de EPI --------------------                    
                    'type': st.column_config.TextColumn(
                    'Tipo',
                    help= 'Tipo do Recurso',
                    default='st.',
                    max_chars=50,
                    ),
                    'CA': st.column_config.NumberColumn(
                    'CA',
                    help= 'Certificado de Aprovação se aplicável',
                    min_value=1,
                    max_value=1000000,
                    step=1,
                    format='%.0f',     
                    ),

                                                                                                              
                                    }, hide_index=True,
        ) 


        if st.button("Salvar Alterações"):
            save_json(edited_data)
            st.success("Alterações salvas com sucesso!")
        
        
        
#------------------------------------ Página Inventario --------------------------------------------
def front_inventario ():
    
        db_manager = DatabaseManager(DB_NAME)
        df = get_latest_data(db_manager)
        
        
        st.title("Detalhes do Inventário de EPI")

        # Calculando o inventário
        inventory_df = df.groupby('EPI Name').agg({"Quantity": "sum"}).reset_index()
        in_stock_df = inventory_df[inventory_df['Quantity'] > 0]

        # Filtros para visualização
        filter_type = st.selectbox("Filtrar por Tipo de EPI:", ["Todos"] + list(in_stock_df['EPI Name'].unique()))
        if filter_type != "Todos":
            filtered_df = in_stock_df[in_stock_df['EPI Name'] == filter_type]
            st.dataframe(data=filtered_df, column_config={
                
                    'Quantity': st.column_config.NumberColumn(
                    'Quantidade',
                    help= 'Quantidade de EPI',
                    min_value=0,
                    max_value=1000000,
                    step=1,
                    format='%.0f',     
                    ),
                    'EPI Name': st.column_config.TextColumn(
                    'Equipamento',
                    help= 'Nome do EPI',
                    default='st.',
                    max_chars=50,
                    
                    ),
                
           },                
            hide_index=True,
                         )

        # Exibindo a quantidade total de EPIs
        if filter_type == "Todos":
            st.write(f"Quantidade Total de EPIs: {in_stock_df['Quantity'].sum()}")
        else:
            st.write(f"Quantidade Total de {filter_type}: {filtered_df['Quantity'].sum()}")

        # Fornecendo uma opção para verificar EPIs abaixo de um certo limite
        limit = st.slider("Mostrar EPIs com quantidade abaixo de:", 1, 280, 5)
        low_stock_df = in_stock_df[in_stock_df['Quantity'] <= limit]
        if not low_stock_df.empty:
            st.warning("Os seguintes EPIs têm estoque baixo:")
            st.dataframe(data=low_stock_df, column_config={
                
                    'Quantity': st.column_config.NumberColumn(
                    'Quantidade',
                    help= 'Quantidade de EPI',
                    min_value=0,
                    max_value=1000000,
                    step=1,
                    format='%.0f',     
                    ),
                    'EPI Name': st.column_config.TextColumn(
                    'Equipamento',
                    help= 'Nome do EPI',
                    default='st.',
                    max_chars=50,
                    
                    ),
                
           },                
            hide_index=True,
                         )
            
        else:
            st.success("Todos os EPIs estão acima do limite selecionado.")
                    
        