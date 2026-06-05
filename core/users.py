import json
from .config import USERS_FILE

def load_Users():
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def authenticate(username, password):
    users = load_Users()
    user = users.get(username)
    if user and user["password"] == password:
        return user
    return None