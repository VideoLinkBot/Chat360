# User ma'lumotlarini vaqtincha xotirada saqlash
users = {}

def add_user(user_id, data):
    users[user_id] = data

def get_user(user_id):
    return users.get(user_id, None)
