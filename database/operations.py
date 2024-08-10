from database.db_manager import DatabaseManager
import streamlit as st
import sqlite3
import logging
logging.basicConfig(level=logging.DEBUG)
import json
import pandas as pd
from fpdf import FPDF
import os
from tabulate import tabulate
from fuzzywuzzy import process
import textwrap
from io import BytesIO
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer


JSON_PATH_image = r"data\data_image.json"
DB_NAME = r"data\epi_stock.db"
JSON_PATH = r'data\data.json'

#Editar Entradas
def edit_entry(self, id, epi_name=None, quantity=None, value=None, transaction_type=None, date=None, requester=None, CA=None):
    logging.debug(f"Called edit_entry with ID={id}")
    
    updates = {
        "epi_name": epi_name,
        "quantity": quantity,
        "value": value,
        "transaction_type": transaction_type,
        "date": date,
        "requester": requester,
        "CA": CA
    }

    # Remove os valores que são None
    updates = {key: val for key, val in updates.items() if val is not None}

    if not updates:
        logging.warning("No values provided for update. Exiting function.")
        return

    placeholders = ', '.join([f"{key} = ?" for key in updates.keys()])
    sql = f"UPDATE epi_stock SET {placeholders} WHERE id = ?"

    logging.debug(f"Executing SQL: {sql} with values {updates.values()}")

    try:
        with sqlite3.connect(DB_NAME) as connection:
            cursor = connection.cursor()
            logging.debug(f"Connected to database: {DB_NAME}")

            values = list(updates.values()) + [id]
            cursor.execute(sql, values)
            connection.commit()
            logging.debug(f"Changes committed to database.")
    except sqlite3.Error as e:
        st.write(f"Erro ao editar registro: {e}")
        logging.error(f"Error while editing entry: {e}")






def delete_entry(self, id):
        connection = sqlite3.connect(DB_NAME)
        cursor = connection.cursor()

        # Tente excluir o registro com base no ID fornecido.
        try:
            cursor.execute("DELETE FROM epi_stock WHERE id = ?", (id,))
            connection.commit()

            # Verifique quantas linhas foram afetadas.
            rows_affected = cursor.rowcount
            if rows_affected == 0:
                st.write(f"Nenhum registro encontrado para o ID: {id}")
            else:
                st.write(f"Registro com ID: {id} excluído com sucesso!")
        except sqlite3.Error as e:
            st.write(f"Erro ao excluir registro: {e}")
        finally:
            connection.close()
        st.rerun()
    
#----------------------- Coluna com Imagens ------------------------------------------------

def display_image_data():
    # Carregar os dados do JSON
    with open(JSON_PATH_image, 'r', encoding='utf-8') as file:
        data = json.load(file)

    df = pd.DataFrame(data)

    # Utilizar o st.data_editor para exibir os dados
    st.dataframe(    
    # Configuração de colunas    
    df,
    column_config={
        'value': st.column_config.NumberColumn(
        label='Valor',
        help='Preço do Equipamento em Reais',
        min_value=0,
        max_value=100000,
        step=1,
        format="$ %.2f"
        ),
        'image_url': st.column_config.ImageColumn(
        label="Imagem", 
        help="Clique na Imagem para expandi-la"
        
        ),
#------------------- Config da coluna Nome-------------------------------------------              
        'epi_name': st.column_config.TextColumn(
        'Equipamento',
        help= 'Nome do EPI',
        default='st.',
        max_chars=50,
                    
        ),
    
#--------------------Coluna de texto tipo de EPI --------------------                    
        'type': st.column_config.TextColumn(
        'Tipo',
        help= 'Equipamento ou Serviço',
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
        
    },
    hide_index=True
)

#-----------------------------Geração de Relatório em PDF ------------------------------

# Calculo de Uniformes para o Relatório em PDF

def calculate_clothing_pairs(data):
    # sourcery skip: dict-comprehension, inline-immediately-returned-variable, move-assign-in-block
    clothing_counts = {"Camisa": {}, "Calça": {}}
    pairs = {}

    # Iterando pelos itens do JSON para calcular totais e contagens
    for item in data:
        epi_name = item.get('epi_name', '')
        quantity = item.get('quantity', 0)

        # Contabilizando camisas e calças
        if 'camisa' in epi_name.lower() or 'calça' in epi_name.lower():
            category = "Camisa" if 'camisa' in epi_name.lower() else "Calça"
            gender = "Masculino" if "masculina" in epi_name.lower() else "Feminino" if "feminina" in epi_name.lower() else "Unissex"
            size = epi_name.split()[-1]  # Pegando a última palavra, que é o tamanho
            key = f"{gender} {size}"
            if key not in clothing_counts[category]:
                clothing_counts[category][key] = 0
            clothing_counts[category][key] += quantity

    # Formando pares de camisas e calças por tamanho e gênero
    for key in clothing_counts["Camisa"]:
        pairs[key] = min(clothing_counts["Camisa"][key], clothing_counts["Calça"].get(key, 0))

    return pairs



# -------------------------------Printando dados no PDF-----------------------------------------------------------





import json
from io import BytesIO
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
import streamlit as st

def calculate_totals(data):
    """Calcula os totais por categoria."""
    totals = {}
    for item in data:
        epi_type = item.get('type', '')
        quantity = item.get('quantity', 0)
        value = item.get('value', 0.0)
        
        if epi_type not in totals:
            totals[epi_type] = 0
        totals[epi_type] += value * quantity
    return totals

def create_table(data, style):
    """Cria uma tabela com estilo padronizado."""
    table = Table(data)
    table.setStyle(style)
    return table

def generate_pdf_report_buffer(filepath):
    """Gera um relatório PDF a partir dos dados do arquivo JSON."""
    try:
        # Carregando os dados do arquivo JSON
        with open(filepath, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo JSON: {e}")
        return None

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CustomTitle", fontSize=18, spaceAfter=20, alignment=1))
    styles.add(ParagraphStyle(name="CustomSubtitle", fontSize=14, spaceAfter=10))
    styles.add(ParagraphStyle(name="CustomTableHeader", fontSize=12, alignment=1, textColor=colors.white))
    styles.add(ParagraphStyle(name="CustomTableCell", fontSize=10, alignment=1))
    
    elements = []

    # Título do Relatório
    elements.append(Paragraph("Relatório de Custeio SSMAS BAERI", styles["CustomTitle"]))
    elements.append(Spacer(1, 12))

    # Cálculo dos totais por categoria
    totals = calculate_totals(data)

    # Tabela de totais por categoria
    elements.append(Paragraph("Totais por Categoria", styles["CustomSubtitle"]))
    table_data = [["Categoria", "Total"]]
    for epi_type, total in totals.items():
        table_data.append([epi_type, f"R$ {total:,.2f}"])

    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ])
    
    table = create_table(table_data, table_style)
    elements.append(table)
    elements.append(Spacer(1, 12))

    # Adicionando o cálculo especial para uniformes
    uniforme_total = totals.get('Uniforme', 0)
    elements.append(Paragraph("Cálculo Especial para Uniformes", styles["CustomSubtitle"]))
    elements.append(Paragraph(f"Valor total com 100% dos Uniformes: R$ {sum(totals.values()):,.2f}", styles["Normal"]))
    elements.append(Paragraph(f"Valor total com Uniformes (considerando 100% e descontando 25% para EINFRA/MANU/MANUSUL): R$ {sum(totals.values()) - 0.25 * uniforme_total:,.2f}", styles["Normal"]))
    elements.append(Paragraph(f"25% do valor dos Uniformes (EINFRA/MANU/MANUSUL): R$ {0.25 * uniforme_total:,.2f}", styles["Normal"]))
    elements.append(Paragraph(f"50% do valor dos Uniformes (5 peças para cada funcionário): R$ {0.50 * uniforme_total:,.2f}", styles["Normal"]))
    elements.append(Paragraph(f"Valor total com Uniformes (considerando 50%): R$ {sum(totals.values()) - uniforme_total + 0.50 * uniforme_total:,.2f}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    # Cálculo de Pares de Uniforme por tamanho
    elements.append(Paragraph("Pares de uniformes por tamanho e gênero:", styles["CustomSubtitle"]))
    pairs = calculate_clothing_pairs(data)  # Presumindo que a função já esteja definida
    for key, count in pairs.items():
        elements.append(Paragraph(f"{key}: {count} pares", styles["Normal"]))
    elements.append(Spacer(1, 12))

    # Tabela para detalhes dos itens
    table_data = [["Descrição", "Quantidade", "Categoria", "Valor Unit.", "CA"]]
    for item in data:
        epi_name = item.get('epi_name', '')
        quantity = item.get('quantity', 0)
        epi_type = item.get('type', '')
        value = item.get('value', 0.0)
        ca = item.get('CA', '')

        table_data.append([epi_name, str(quantity), epi_type, f"R$ {value:,.2f}", str(ca)])

    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ])
    
    table = create_table(table_data, table_style)
    elements.append(table)

    # Construir o PDF
    try:
        doc.build(elements)
    except Exception as e:
        st.error(f"Erro ao criar o PDF: {e}")
        return None

    # Retornar o buffer com o conteúdo do PDF
    buffer.seek(0)
    return buffer

def front_pdf_generate():
    """Interface do Streamlit para gerar o PDF."""
    st.sidebar.subheader("Exportar Relatório")
    if st.sidebar.button("Gerar Relatório PDF"):
        buffer = generate_pdf_report_buffer(JSON_PATH)
        if buffer:
            pdf_bytes = buffer.getvalue()
            st.sidebar.download_button(label="Download do relatório", data=pdf_bytes, file_name="report.pdf", mime="application/pdf")
        else:
            st.sidebar.error("Falha ao gerar o PDF.")



         
#--------------------------------------- Teste para considerar detalhes nas entradas ------------------------------------------------


def get_closest_match_name(name, choices):
    # Retorna o nome mais aproximado usando a função `extractOne` do fuzzywuzzy
    closest_match, score = process.extractOne(name, choices)
    return closest_match if score > 99 else name  # Você pode ajustar o limite de pontuação conforme necessário