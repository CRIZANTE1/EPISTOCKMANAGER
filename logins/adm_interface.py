import streamlit as st
import json
import bcrypt

# Função para criar hash de senha
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Função para adicionar um novo usuário
def add_user(username, password, name, filepath='data/users_db.json'):
    with open(filepath, 'r') as file:
        users = json.load(file)

    if username in users:
        st.error("Usuário já existe.")
        return

    hashed_password = hash_password(password)
    users[username] = {
        "password": hashed_password,
        "name": name,
        "role": "user"  # Defina o papel padrão para novos usuários
    }

    with open(filepath, 'w') as file:
        json.dump(users, file, indent=4)

    st.success(f"Usuário {username} adicionado com sucesso!")

# Interface para adicionar novo usuário
def admin_interface():
    st.title("Cadastro de Novo Usuário")
    
    username = st.text_input("Nome de Usuário")
    password = st.text_input("Senha", type="password")
    name = st.text_input("Nome Completo")
    
    if st.button("Cadastrar"):
        if username and password and name:
            add_user(username, password, name)
        else:
            st.warning("Por favor, preencha todos os campos.")
            
            
