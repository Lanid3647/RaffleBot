from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup



def get_start_keyboard():
    keyboard = [
        [InlineKeyboardButton("➕ Добавить канал", callback_data="add_channel")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_admin_keyboard():
    keyboard = [
        [InlineKeyboardButton("✨ Подключить ✨", callback_data="get_new_version")],
    ]
    return InlineKeyboardMarkup(keyboard)

def new_version_2():
    keyboard = [
        [InlineKeyboardButton("✨ Подключить Расширенную версию ✨", callback_data="get_version")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_bot_menu():
    keyboard = [
        ["Создать розыгрыш 🎁"],
        ["✨ Расширенная версия бота✨\n❗️Включая ВК ❗️"],
        ["Мои каналы 📢", "Техническая поддержка ⁉️"],
        ["Мои розыгрыши 🗒", "О боте ℹ️"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_bot_menu_draw_3():
    keyboard = [
        ["❌Отменить создание"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)




def get_bot_menu_draw_1():
    keyboard = [
        ["⬅️Назад"],
        ["❌Отменить создание"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)



# Шаг № 1
def get_keyboard_draw_1():
    keyboard = [
        [InlineKeyboardButton("🤖 Автоматический", callback_data="type_auto")],
        [InlineKeyboardButton("📋 Самостоятельный", callback_data="type_me")]
    ]
    return InlineKeyboardMarkup(keyboard)


# Шаг № 2

def get_keyboard_draw_2():
    keyboard = [
        [InlineKeyboardButton("🏆 Ввести количество победителей", callback_data="confirm")],
    ]
    return InlineKeyboardMarkup(keyboard)

# Шаг № 3
def get_time():
    keyboard = [
        [InlineKeyboardButton("🕐 Прямо сейчас", callback_data="time_start")],
        [InlineKeyboardButton("🕐 Запланировать публикацию", callback_data="time_end")],
    ]
    return InlineKeyboardMarkup(keyboard)
# Шаг № 4
# Шаг № 5
# Шаг № 6
# Шаг № 7
# Шаг № 3
def get_referral():
    keyboard = [
        [InlineKeyboardButton("0 - отключить", callback_data="referral_0"), InlineKeyboardButton("3", callback_data="referral_3")],
        [InlineKeyboardButton("1", callback_data="referral_1"), InlineKeyboardButton("4", callback_data="referral_4")],
        [InlineKeyboardButton("2", callback_data="referral_2"), InlineKeyboardButton("5", callback_data="referral_5")],

    ]
    return InlineKeyboardMarkup(keyboard)
# Шаг № 8
# Шаг № 9
# Шаг № 10

def get_channels():
    keyboard = [
        ["🔸 Каналы Телеграмм","🔹 Каналы Вконтакте" ],
        ["⬅️Назад"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def add_channels():
    keyboard = [
        [InlineKeyboardButton("➕ Добавить новый канал", callback_data="add_channel")],
    ]
    return InlineKeyboardMarkup(keyboard)


