import pandas as pd
import datetime

def import_from_excel(db_manager, excel_path):
    try:
        df = pd.read_excel(excel_path, engine='openpyxl')
        for _, row in df.iterrows():
            epi_name = row["epi_name"]
            quantity = int(row["quantity"])
            transaction_type = row.get("Transaction_type", "entrada")
            date = row.get("date") or datetime.date.today().strftime("%Y-%m-%d")
            value = float(row["value"])
            requester = row.get("Requester", None)
            ca = int(row["CA"])
            

            # Adicionar entrada ao banco de dados
            db_manager.add_entry(epi_name, quantity, transaction_type, date, value, requester, ca)
                        
        print(f"{len(df)} registros importados com sucesso!")
    except FileNotFoundError:
        print("Erro: Arquivo não encontrado.")
    except KeyError as e:
        print(f"Erro: Coluna {e} não encontrada no Excel.")
    except Exception as e:
        print(f"Erro inesperado ao importar dados do Excel: {e}")


