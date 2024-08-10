import os
import json
import streamlit as st
from utilities.optionals import animation_fantasm
from configs.config_front import set_page, temperatura_vento, entrance_exit_edit_delete,frame_page_one
from database.db_manager import DatabaseManager
from database.operations import display_image_data, generate_pdf_report_buffer, get_closest_match_name
from utilities.excel_importer import import_from_excel
import pandas as pd
from utilities.calculations import calculate_forecast, save_forecast_to_json, retrieve_forecast_from_json, get_forecast_data,  show_progress_bar, load_json, save_json, add_to_json
from utilities.insights import generate_uniform_pairs_insight, display_monthly_insights
import logging
logging.basicConfig(level=logging.DEBUG)
from streamlit_lottie import st_lottie



#----------------------------------Dados------------------------------------------------
FILEPATH = r'data\temperature.txt'
DB_NAME = r'data\epi_stock.db'
JSON_PATH = r'data\data.json'

#--------------------------- Nome da Pagina e configurações------------------------------
set_page()
#------------------ Temperatura, Velocidade do vento, Umidade -----------------------------
temperatura_vento()
#------------------------ Configurações --------------------------------
def get_latest_data(db_manager):
    data = db_manager.execute_query("SELECT * FROM epi_stock", fetch_all=True)
    return pd.DataFrame(data, columns=["ID","EPI Name", "Quantity", "Transaction Type", "Date", "Value", "Requester", "CA"])


#--------------------------- Classe Main --------------------------------
def main(): 
#---------------------------------------- Barra de Progresso ------------------------  
    progress_placeholder = st.empty()
    show_progress_bar(progress_placeholder)
    progress_placeholder.empty()
    
#------------------------------------ Carregamento de dados --------------------------
    
    db_manager = DatabaseManager(DB_NAME)
    df = get_latest_data(db_manager)
    
    if not os.path.isfile(DB_NAME):
        db_manager.create_table()
        
        
#---------------------------Escolha da Pagina -------------------------------------        
    page = st.sidebar.selectbox("Escolha a página:", ["Página Inicial", "Teste"])
    
    
    if page == "Página Inicial": # Página inicial da aplicação
        
        st.title("Gerenciamento de Equipamentos de Proteção Individual")
        st.caption('EPI Stock Management')
        
        animation_fantasm()
        
        
        
# ------------------- Página 2 ---------------------------------------------        
        
    elif page == "Teste":
        
        
        st.subheader("Teste")
      
        st.caption('EPI Stock Management')
        
        animation_fantasm()

      
      
      
      
      
      
      
      
      
      
      
      
      
      
      
      
            
if __name__ == "__main__":
    
    main()
    st.caption('Desenvolvido por Cristian Ferreira Carlos')            