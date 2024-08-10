import streamlit as st
import json
from datetime import datetime
import bcrypt

# Função para carregar dados de usuários de um arquivo JSON
def load_users_db(filepath=r'data/users_db.json'):
    with open(filepath, 'r') as file:
        return json.load(file)

# Função para registrar tentativas de login
def log_attempt(username, success):
    log_entry = {
        "username": username,
        "success": success,
        "timestamp": datetime.now().isoformat()
    }
    with open('data/login_attempts.json', 'a') as file:
        json.dump(log_entry, file)
        file.write('\n')

# Função para realizar login
def login(users_db):
    st.title("EPI Stock Management")
    
    username = st.text_input("Nome de Usuário", placeholder="Digite seu nome de usuário")
    password = st.text_input("Senha", type="password", placeholder="Digite sua senha")
    
    if st.button("Login"):
        if username and password:  # Verificação de campos vazios
            if username in users_db:
                user_data = users_db[username]
                hashed_password = user_data.get("password")
                if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.name = user_data["name"]
                    st.session_state.role = user_data.get("role", "user")
                    st.success(f"Bem-vindo, {st.session_state.name}!")
                    log_attempt(username, success=True)
                else:
                    st.error("Senha incorreta.")
                    log_attempt(username, success=False)
            else:
                st.error("Nome de usuário não encontrado.")
                log_attempt(username, success=False)
        else:
            st.warning("Por favor, preencha todos os campos.")

# Função de logout
def logout():
    st.session_state.clear()  # Limpa o estado da sessão
     

