from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, WebAppInfo
import os
from dotenv import load_dotenv

load_dotenv()



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

def get_dashboard_keyboard():
    """Клавиатура для дашборда с двумя кнопками"""
    keyboard = [
        [InlineKeyboardButton("✨ Подключить расширенную версию бота", callback_data="get_new_version")],
        [InlineKeyboardButton("🎁 Создать розыгрыш", callback_data="start_create_raffle")]
    ]
    return InlineKeyboardMarkup(keyboard)

def new_version_2():
    keyboard = [
        [InlineKeyboardButton("✨ Подключить Расширенную версию ✨", callback_data="get_version")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_bot_menu(webapp_url: str = None, is_admin: bool = False):
    """
    Создает главное меню бота
    webapp_url - URL мини-приложения (должен быть HTTPS)
    Если URL не указан, пытается взять из переменной окружения WEBAPP_URL
    is_admin - флаг, является ли пользователь администратором
    """
    keyboard = [
        ["Создать розыгрыш 🎁"],
        ["✨ Расширенная версия бота✨"],
        ["Мои каналы 📢", "Техническая поддержка ⁉️"],
        ["Мои розыгрыши 🗒", "О боте ℹ️"]
    ]
    
    # Добавляем кнопку админ-панели для администраторов
    if is_admin:
        keyboard.append(["👑 Админ-панель"])
    
    # Получаем URL из параметра или переменной окружения
    if not webapp_url:
        webapp_url = os.getenv('WEBAPP_URL', None)
    
    # Убираем слэш в конце URL, если есть
    if webapp_url:
        webapp_url = webapp_url.rstrip('/')
    
    # Добавляем кнопку WebApp, если URL указан
    if webapp_url:
        print(f"[DEBUG] Добавляю кнопку WebApp с URL: {webapp_url}")  # Отладочный вывод
        keyboard.append([KeyboardButton("🌐 Открыть мини-приложение", web_app=WebAppInfo(url=webapp_url))])
    else:
        print("[DEBUG] WEBAPP_URL не найден, кнопка не будет добавлена")  # Отладочный вывод
    
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
        ["🔸 Каналы Телеграмм"],
        ["⬅️Назад"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def add_channels():
    keyboard = [
        [InlineKeyboardButton("➕ Добавить новый канал", callback_data="add_channel")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_webapp_button(webapp_url: str = None):
    """
    Создает InlineKeyboardMarkup с кнопкой для открытия мини-приложения
    webapp_url - URL мини-приложения (должен быть HTTPS)
    Если URL не указан, пытается взять из переменной окружения WEBAPP_URL
    """
    # Получаем URL из параметра или переменной окружения
    if not webapp_url:
        webapp_url = os.getenv('WEBAPP_URL', None)
    
    # Убираем слэш в конце URL, если есть
    if webapp_url:
        webapp_url = webapp_url.rstrip('/')
    
    # Создаем кнопку WebApp, если URL указан
    if webapp_url:
        print(f"[DEBUG] Создаю кнопку WebApp с URL: {webapp_url}")
        keyboard = [
            [InlineKeyboardButton("🌐 Открыть мини-приложение", web_app=WebAppInfo(url=webapp_url))]
        ]
        return InlineKeyboardMarkup(keyboard)
    else:
        print("[DEBUG] WEBAPP_URL не найден, кнопка WebApp не будет создана")
        return None


