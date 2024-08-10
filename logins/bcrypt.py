import bcrypt
import json

# Função para criar hash de senha
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Função para adicionar um novo usuário
def add_user(username, password, name, filepath='data/users_db.json'):
    with open(filepath, 'r') as file:
        users = json.load(file)

    if username in users:
        print("Usuário já existe.")
        return

    hashed_password = hash_password(password)
    users[username] = {
        "password": hashed_password,
        "name": name
    }

    with open(filepath, 'w') as file:
        json.dump(users, file, indent=4)

    print(f"Usuário {username} adicionado com sucesso!")

# Exemplo de uso
add_user("NovoUsuario", "SenhaSegura123", "Nome Completo")

