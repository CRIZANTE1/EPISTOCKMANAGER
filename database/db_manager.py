import sqlite3
import streamlit as st
import pandas as pd
import datetime
import os

DB_NAME = os.path.join(os.path.dirname(__file__), r"data\epi_stock.db")

class DatabaseManager:
    def __init__(self, db_name):
        self.db_name = db_name 

    def connect_db(self):
        conn = sqlite3.connect(self.db_name)
        return conn

    def execute_query(self, query, params=(), fetch_all=False):
        connection = None  # Initialize connection variable outside try block
        try:
            connection = self.connect_db()
            cursor = connection.cursor()
            cursor.execute(query, params)
            connection.commit()
            return cursor.fetchall() if fetch_all else cursor.fetchone()
        except sqlite3.IntegrityError:
            st.write("Integrity Error: Please make sure the data being inserted or updated doesn't violate database constraints.")
        except sqlite3.Error as e:
            st.write(f"Erro ao executar query: {e}")
        except Exception as e:
            st.write(f"Unexpected error: {e}")     
        finally:
            if connection:  # Verifica se a conexão foi inicializada
                connection.close()

    def create_table(self):
        create_table_query = """
        CREATE TABLE IF NOT EXISTS epi_stock (
            id INTEGER PRIMARY KEY,
            epi_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            transaction_type TEXT,
            date TEXT DEFAULT (date('now')),
            value REAL,
            requester TEXT,
            CA INTEGER 
        )
        """
        self.execute_query(create_table_query)
        
#Configurar entardas
    def add_entry(self, epi_name, quantity, transaction_type, date, value, ca, requester=None):
        if not date:
            date = datetime.date.today().strftime("%Y-%m-%d")
                
        add_entry_query = """
        INSERT INTO epi_stock (epi_name, quantity, transaction_type, date, value, CA, requester)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        self.execute_query(add_entry_query, (epi_name, quantity, transaction_type, date, value, ca, requester))

#Adicionar Saídas
    def add_exit(self, id, quantity, requester, exit_date):
        try:
            connection = self.connect_db()
            cursor = connection.cursor()

            # Get EPI name by ID
            cursor.execute("SELECT epi_name FROM epi_stock WHERE id = ?", (id,))
            epi_name = cursor.fetchone()[0]

            # Register the exit as a separate transaction
            cursor.execute("""
            INSERT INTO epi_stock (epi_name, quantity, transaction_type, date, value, requester)
            VALUES (?, ?, 'saida', ?, 0, ?)
            """, (epi_name, -quantity, exit_date, requester))

            connection.commit()

        except sqlite3.Error as e:
            st.write(f"Erro ao registrar saída: {e}")
        finally:
            if connection:
                connection.close()

            
    def create_budget_forecast_table(self):
        create_table_query = """
        CREATE TABLE IF NOT EXISTS budget_forecast (
        year INTEGER PRIMARY KEY,
        forecast REAL NOT NULL
    )
    """
        self.execute_query(create_table_query)

    def set_budget_forecast(self, year, forecast):
        add_forecast_query = """
        INSERT OR REPLACE INTO budget_forecast (year, forecast)
        VALUES (?, ?)
        """
        self.execute_query(add_forecast_query, (year, forecast))

    def get_budget_forecast(self, year):
        get_forecast_query = """
        SELECT forecast FROM budget_forecast WHERE year = ?
        """
        result = self.execute_query(get_forecast_query, (year,))
        return result[0] if result else None



                   

