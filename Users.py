# Foydalanuvchi ma’lumotlarini boshqarish

users = {}

def add_user(user_id, name):
    if user_id not in users:
        users[user_id] = {
            "name": name,
            "language": None,
            "vip": False,
            "referral": None
        }

def set_language(user_id, lang_code):
    if user_id in users:
        users[user_id]["language"] = lang_code

def set_vip(user_id, status=True):
    if user_id in users:
        users[user_id]["vip"] = status

def set_referral(user_id, referral_code):
    if user_id in users:
        users[user_id]["referral"] = referral_code

def get_user(user_id):
    return users.get(user_id, None)
