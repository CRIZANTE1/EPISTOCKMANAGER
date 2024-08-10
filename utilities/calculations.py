import contextlib
import json
import requests
from lxml import html
import streamlit as st 
import time
import os

#----------------- Configurações------------------------
JSON_FORE_PATH = r'data\forecast_data.json'
JSON_PATH = r'data\data.json'
filepath = 'data/temperature.txt'

#----------------- Utilidades ---------------------

def save_forecast_to_json(year, forecast, json_path= JSON_FORE_PATH):
    # Inicialmente, tente abrir o arquivo e ler os dados. Se o arquivo não existir ou houver um erro de decodificação, inicie com um dicionário vazio.
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}

    # Se a chave 'forecasts' não existir ou não for uma lista, crie/set como uma lista vazia.
    if not isinstance(data.get('forecasts'), list):
        data['forecasts'] = []

    # Agora, busque se o ano já existe em 'forecasts'. Se existir, atualize. Se não, adicione.
    for entry in data['forecasts']:
        if entry['year'] == year:
            entry['forecast'] = forecast
            break
    else:
        # A cláusula 'else' após um loop 'for' só é executada se o loop não foi interrompido por um 'break'.
        # Portanto, se não encontrarmos o ano, adicionamos um novo dicionário à lista 'forecasts'.
        data['forecasts'].append({'year': year, 'forecast': forecast})

    # Salve os dados atualizados no arquivo.
    with open(json_path, 'w') as f:
        json.dump(data, f) 


def retrieve_forecast_from_json(year, json_path= JSON_FORE_PATH):
    with contextlib.suppress(FileNotFoundError, json.JSONDecodeError):
        with open(json_path, 'r') as f:
            data = json.load(f)

        forecasts = data.get('forecasts', [])
        for entry in forecasts:
            if entry['year'] == year:
                return entry['forecast']
    return None        
        
#------------------ Calculos ------------------------



def calculate_forecast(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:  # Adicione encoding='utf-8' aqui
        data = json.load(file)

    return sum(item['quantity'] * item['value'] for item in data)

def calculate_forecast_by_type(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    forecast_by_type = {}
    for item in data:
        forecast_by_type[item['type']] = forecast_by_type.get(item['type'], 0) + item['quantity'] * item['value']

    return forecast_by_type

# Esta função agora só retorna os dados processados
def get_forecast_data(filepath):
    return calculate_forecast_by_type(filepath)

#------------------- Metricas te temperatura ----------------------

def get_value_from_xpath(url, xpath):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36'
    }  # Simulando um navegador para evitar bloqueios anti-bot

    response = requests.get(url, headers=headers)
    tree = html.fromstring(response.content)

    if elements := tree.xpath(xpath):
        return elements[0].text_content().strip()
    else:
        return None

import json

def save_data_to_file(data, filepath):
    with open(filepath, 'w', encoding='utf-8') as file:
        json.dump(data, file)

def read_data_from_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return None


def get_weather_data(filepath):
    
    # Obtém o tempo atual
    current_time = time.time()

    # Tenta ler os dados antigos do arquivo
    old_data = read_data_from_file(filepath)

    # Se os dados antigos existirem e não tiver passado 10 minutos desde a última atualização, retornar os dados antigos
    if old_data and (current_time - old_data.get('timestamp', 0) < 600):  # 600 segundos = 10 minutos
        return old_data

    url = 'https://www.google.com/search?q=temperatura'
    xpath_temperature = '//*[@id="wob_tm"]'
    xpath_humidity = '//*[@id="wob_hm"]'
    xpath_wind = '//*[@id="wob_ws"]'
    
    temperature = get_value_from_xpath(url, xpath_temperature)
    humidity = get_value_from_xpath(url, xpath_humidity)
    wind = get_value_from_xpath(url, xpath_wind)
    
    new_data = {
        "temperature": temperature,
        "humidity": humidity,
        "wind": wind,
        "timestamp": current_time  # Adiciona o timestamp atual aos dados
    }

    # Salva os novos dados no arquivo
    save_data_to_file(new_data, filepath)

    return new_data

#--------------------------- Barra de progresso ao passar de pagina -------------------------------------------

def show_progress_bar(progress_placeholder):
    progress_text = "Aguarde o carregamento da página..."
    with st.spinner(progress_text):
        for _ in range(100):
            time.sleep(0.006)
    
#--------------------------------------Edição de Dataframe-------------------------------
def load_json(json_path=JSON_PATH):
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    else:
        return []

def save_json(data, json_path=JSON_PATH):
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def add_to_json(entry, json_path=JSON_PATH):
    data = load_json(json_path)
    data.append(entry)
    save_json(data, json_path)
















