import json
import streamlit as st
import pandas as pd
from database.db_manager import DatabaseManager



def calculate_clothing_counts(data):
    clothing_counts = {
        "Camisa": {},
        "Calça": {},
        "Japona": {}
    }

    # Iterando pelos itens do JSON para calcular contagens
    for item in data:
        epi_name = item.get('epi_name', '').lower()
        quantity = item.get('quantity', 0)

        if 'camisa' in epi_name:
            category = "Camisa"
        elif 'calça' in epi_name:
            category = "Calça"
        elif 'japona' in epi_name:
            category = "Japona"
        else:
            continue  # Se não for nenhum dos três tipos, continue para o próximo item

        gender = "Masculino" if "masculina" in epi_name else "Feminino" if "feminina" in epi_name else "Unissex"
        size = epi_name.split()[-1]  # Pegando a última palavra, que é o tamanho

        key = f"{gender} {size}"
        
        if key not in clothing_counts[category]:
            clothing_counts[category][key] = 0
        
        clothing_counts[category][key] += quantity

    return clothing_counts


def generate_uniform_pairs_insight(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        data = json.load(file)

    pairs = calculate_clothing_counts(data)

    # Título
    st.write("## Insights:")
    st.write("Descrição da quantidade de uniformes prevista:")

    # Separando as categorias
    camisas = {key: value for key, value in pairs.items() if "Camisa" in key}
    calças = {key: value for key, value in pairs.items() if "Calça" in key}
    japonas = {key: value for key, value in pairs.items() if "Japona" in key}

    # Criando colunas
    col1, col2, col3 = st.columns(3)

    with col1:
        st.write("Camisas:")
        for key, count in camisas.items():
            st.write(f"{key.split(' ')[-1]}: {count}")
    with col2:
        st.write("Calças:")
        for key, count in calças.items():
            st.write(f"{key.split(' ')[-1]}: {count}")
    with col3:
        st.write("Japonas:")
        for key, count in japonas.items():
            st.write(f"{key.split(' ')[-1]}: {count}")

#------------------------------ Demonstrativo de uso -----------------------

def get_insight_for_requester(df, requester, month, year):
    """
    Retorna um insight sobre quanto de cada EPI um determinado requisitante pegou em um mês específico.
    
    Args:
    - df: DataFrame que contém os dados.
    - requester: Nome do requisitante.
    - month: Mês desejado.
    - year: Ano desejado.

    Returns:
    - Texto com o insight.
    """

    # Filtrar os dados com base no requisitante, tipo de transação e data
    filtered_df = df[
        (df['Transaction Type'] == 'saida') &
        (pd.to_datetime(df['Date']).dt.month == month) &
        (pd.to_datetime(df['Date']).dt.year == year) &
        (df['Requester'] == requester)
    ]

    # Agrupar por nome de EPI e somar as quantidades
    epi_counts = filtered_df.groupby('EPI Name')['Quantity'].sum()

    # Construir a mensagem de insight
    insights = []
    for epi_name, quantity in epi_counts.iteritems():
        insights.append(f"{requester} pegou {quantity} unidades de {epi_name} em {month}/{year}.")

    return "\n".join(insights)


#--------------------------------------- Insights Sobre o Uso no mês -----------------------------------


def generate_monthly_insights(df, month, year):
    monthly_data = df[df['Date'].dt.to_period('M') == pd.Period(year=year, month=month, freq='M')]

    total_entries = monthly_data.loc[monthly_data['Transaction Type'] == 'entrada', 'Quantity'].sum()
    total_exits = abs(monthly_data.loc[monthly_data['Transaction Type'] == 'saida', 'Quantity'].sum())
    total_spent = monthly_data.loc[monthly_data['Transaction Type'] == 'entrada', 'Value'].sum()
    
    most_distributed = abs(monthly_data.loc[monthly_data['Transaction Type'] == 'saida'].groupby('EPI Name')['Quantity'].sum()).nlargest(3)
    least_distributed = abs(monthly_data.loc[monthly_data['Transaction Type'] == 'saida'].groupby('EPI Name')['Quantity'].sum()).nsmallest(3)
    top_requesters = abs(monthly_data.loc[monthly_data['Transaction Type'] == 'saida'].groupby('Requester')['Quantity'].sum()).nlargest(3)
    
    # Solicitante mais frequente
    most_frequent_requester = monthly_data['Requester'].mode()[0]

    # EPIs trocados em menos de uma semana
    def detect_quick_replacements(group):
        return any(group.sort_values(by="Date")["Date"].diff().dt.total_seconds() / (3600 * 24) < 7)
    
    replacements = monthly_data[monthly_data['Transaction Type'] == 'saida'].groupby(['Requester', 'EPI Name']).apply(detect_quick_replacements)
    quick_replacements = replacements[replacements].reset_index()
    
    return {
        'quick_replacements': quick_replacements,
        "total_entries": total_entries,
        "total_exits": total_exits,
        "total_spent": total_spent,
        "most_distributed": most_distributed,
        "least_distributed": least_distributed,
        "top_requesters": top_requesters,
        "most_frequent_requester": most_frequent_requester,
        
    }

def display_monthly_insights(df):
    try:
        today = pd.Timestamp.now()
        
        # Criar um widget para selecionar o mês e ano
        selected_date = st.date_input("Selecione o mês e ano para os insights", today)

        # Obter mês e ano da data selecionada
        selected_month, selected_year = selected_date.month, selected_date.year

        # Gere insights para o mês e ano selecionados
        insights = generate_monthly_insights(df, selected_month, selected_year)

        st.subheader(f"Insights: {selected_month}/{selected_year}")

        # Criar um layout de colunas para melhor apresentação
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f"**Entradas:** {insights['total_entries']}")
        with col2:
            st.markdown(f"**Saídas:** {insights['total_exits']}")
        with col3:
            st.markdown(f"**Gasto:** R$ {insights['total_spent']:.2f}")

        st.markdown("### Top 3 EPIs Distribuídos:")
        st.write(', '.join([f"{epi}: {qtd}" for epi, qtd in insights['most_distributed'].items()]))

        st.markdown("### EPIs Menos Distribuídos:")
        st.write(', '.join([f"{epi}: {qtd}" for epi, qtd in insights['least_distributed'].items()]))

        st.markdown("### Top Solicitantes:")
        st.write(', '.join([f"{requester}: {qtd}" for requester, qtd in insights['top_requesters'].items()]))

        st.markdown(f"### Solicitante Mais Frequente: {insights['most_frequent_requester']}")

        if not insights['quick_replacements'].empty:
            st.warning("Alerta! Trocas rápidas (em menos de uma semana) detectadas:")
            for _, row in insights['quick_replacements'].iterrows():
                st.write(f"**Requisitante:** {row['Requester']} | **EPI:** {row['EPI Name']}")
    except Exception as e:
        st.warning("Não há dados disponíveis para mostrar os insights neste mês/ano.")