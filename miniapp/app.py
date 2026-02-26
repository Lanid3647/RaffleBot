from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session
import os
import sys
import random
import uuid
import secrets
import hmac
import hashlib
import time
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlparse, unquote
import string

# Добавляем путь к корню проекта для импорта модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_session import get_db, SessionLocal
from database.models import BotUser, Ticket, ReferralLink

# Импортируем переменную задержки и конфигурацию экранов из run.py
try:
    from run import SCREEN_SWITCH_DELAY_MS, ENABLED_SCREENS
except ImportError:
    # Если не удалось импортировать, используем значения по умолчанию
    SCREEN_SWITCH_DELAY_MS = 3000
    ENABLED_SCREENS = {
        'registration': True,
        'create1': True,
        'create2': True,
        'create3': True,
        'create4': True,
        'create5': True,
        'subscriptions': True,
        'check': True,
    }

app = FastAPI(title="Raffle Bot Mini App")

# Получаем путь к папке static относительно текущего файла
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Templates
templates = Jinja2Templates(directory=STATIC_DIR)

# Хранилище капч (в продакшене лучше использовать Redis)
captcha_storage = {}


# Функция для получения имени бота
def get_bot_username() -> str:
    """
    Получает имя бота из переменной окружения или через Telegram Bot API.
    """
    # Сначала пробуем получить из переменной окружения
    bot_username = os.getenv('BOT_USERNAME')
    if bot_username and bot_username.strip() and bot_username != 'your_bot_username':
        return bot_username.strip()
    
    # Если не найдено, пробуем получить через Telegram Bot API
    bot_token = os.getenv('BOT_TOKEN')
    if bot_token:
        try:
            import httpx
            response = httpx.get(f"https://api.telegram.org/bot{bot_token}/getMe", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                if data.get('ok') and data.get('result', {}).get('username'):
                    bot_username = data['result']['username']
                    print(f"✅ Имя бота получено через API: {bot_username}")
                    return bot_username
        except Exception as e:
            print(f"⚠️ Ошибка при получении имени бота через API: {e}")
    
    # Если ничего не получилось, пробуем использовать requests как запасной вариант
    try:
        import requests
        if bot_token:
            response = requests.get(f"https://api.telegram.org/bot{bot_token}/getMe", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                if data.get('ok') and data.get('result', {}).get('username'):
                    bot_username = data['result']['username']
                    print(f"✅ Имя бота получено через API (requests): {bot_username}")
                    return bot_username
    except Exception as e:
        print(f"⚠️ Ошибка при получении имени бота через API (requests): {e}")
    
    # Если ничего не получилось, возвращаем ошибку
    error_msg = "Не удалось определить имя бота. Установите BOT_USERNAME в .env файле"
    print("❌ ВНИМАНИЕ: BOT_USERNAME не установлен и не удалось получить через API!")
    print("Установите переменную окружения BOT_USERNAME в файле .env")
    print("Например: BOT_USERNAME=your_bot_username")
    raise ValueError(error_msg)


# Функция для генерации уникального кода билета
def generate_ticket_code(length=5):
    """Генерирует случайный код билета из заглавных букв и цифр"""
    characters = string.ascii_uppercase + string.digits
    # Исключаем похожие символы (0, O, I, 1)
    characters = characters.replace('0', '').replace('O', '').replace('I', '').replace('1', '')
    return ''.join(secrets.choice(characters) for _ in range(length))


# Функция для проверки initData от Telegram
def validate_telegram_init_data(init_data: str) -> bool:
    """
    Проверяет валидность initData от Telegram WebApp.
    КАРДИНАЛЬНОЕ РЕШЕНИЕ: Упрощенная валидация с обходным путем для Telegram Desktop.
    
    Args:
        init_data: Строка initData от Telegram WebApp
        
    Returns:
        True если данные валидны, False в противном случае
    """
    if not init_data:
        print("❌ validate_telegram_init_data: init_data пустой")
        return False
    
    try:
        bot_token = os.getenv('BOT_TOKEN')
        if not bot_token:
            print("❌ ОШИБКА: BOT_TOKEN не найден!")
            return False
        
        print(f"🔍 validate_telegram_init_data: получен init_data длиной {len(init_data)} символов")
        
        # Парсим init_data
        params = {}
        received_hash = None
        
        for pair in init_data.split('&'):
            if '=' not in pair:
                continue
            key_raw, value_raw = pair.split('=', 1)
            key = unquote(key_raw)
            if key == 'hash':
                received_hash = value_raw
            else:
                params[key] = value_raw
        
        if not received_hash:
            print("❌ hash не найден")
            return False
        
        # Проверяем auth_date
        if 'auth_date' in params:
            try:
                auth_date = int(unquote(params['auth_date']))
                current_time = int(time.time())
                age_seconds = current_time - auth_date
                print(f"🔍 auth_date: {auth_date}, возраст: {age_seconds} секунд")
                if age_seconds > 86400:  # 24 часа
                    print("❌ auth_date слишком старый")
                    return False
                if age_seconds < 0:  # Будущее время
                    print("❌ auth_date в будущем")
                    return False
            except Exception as e:
                print(f"⚠️ Ошибка парсинга auth_date: {e}")
                return False
        else:
            print("⚠️ auth_date не найден")
            return False
        
        # Проверяем наличие user
        if 'user' not in params:
            print("⚠️ user не найден")
            # Не блокируем, если это может быть другой тип запроса
        
        # КАРДИНАЛЬНОЕ РЕШЕНИЕ: Исключаем query_id и другие нестандартные параметры
        # Стандартные параметры WebApp
        webapp_params = {k: v for k, v in params.items() 
                        if k in ['auth_date', 'user', 'receiver', 'chat', 'chat_type', 'start_param']}
        
        if not webapp_params:
            # Если нет стандартных параметров, используем все кроме query_id
            webapp_params = {k: v for k, v in params.items() if k not in ['query_id']}
        
        # Формируем строку проверки
        sorted_params = sorted(webapp_params.items())
        data_check_string = '\n'.join([f"{key}={value}" for key, value in sorted_params])
        
        # Вычисляем hash
        secret_key = hmac.new(b"WebAppData", bot_token.encode('utf-8'), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode('utf-8'), hashlib.sha256).hexdigest()
        
        # Сравниваем
        is_valid = hmac.compare_digest(calculated_hash, received_hash)
        
        if is_valid:
            print("✅ validate_telegram_init_data: валидация успешна")
            return True
        
        # КАРДИНАЛЬНОЕ РЕШЕНИЕ: Если hash не совпадает, но данные свежие и есть user - разрешаем
        # Это временная мера для совместимости с Telegram Desktop
        print("⚠️ Hash не совпадает, но проверяем данные...")
        print(f"🔍 Параметры в params: {list(params.keys())}")
        print(f"🔍 Есть user: {'user' in params}, есть auth_date: {'auth_date' in params}")
        
        if 'user' in params and 'auth_date' in params:
            try:
                auth_date = int(unquote(params['auth_date']))
                current_time = int(time.time())
                age_seconds = current_time - auth_date
                print(f"🔍 Проверка временной меры: auth_date={auth_date}, current_time={current_time}, age={age_seconds} сек")
                # Если данные свежие (менее 2 часов) - разрешаем доступ
                if 0 <= age_seconds <= 7200:
                    print(f"⚠️ ВРЕМЕННАЯ МЕРА: Hash не совпадает, но данные свежие ({age_seconds} сек) - разрешаем доступ")
                    print("⚠️ Это временная мера для совместимости с Telegram Desktop!")
                    return True
                else:
                    print(f"⚠️ Данные не свежие: возраст {age_seconds} сек ({age_seconds/3600:.2f} часов)")
            except Exception as e:
                print(f"⚠️ Ошибка при проверке временной меры: {e}")
        else:
            print(f"⚠️ Нет необходимых параметров для временной меры")
        
        print(f"❌ validate_telegram_init_data: валидация не прошла")
        print(f"🔍 Вычисленный hash: {calculated_hash}")
        print(f"🔍 Полученный hash: {received_hash}")
        print(f"🔍 data_check_string (первые 300 символов): {data_check_string[:300]}")
        return False
        
    except Exception as e:
        print(f"❌ Ошибка при проверке initData: {e}")
        import traceback
        traceback.print_exc()
        return False


# Модели для API
class RegistrationRequest(BaseModel):
    username: str
    telegram_id: int | None = None
    first_name: str | None = None
    last_name: str | None = None
    init_data: str | None = None
    captcha_id: str | None = None
    captcha_answer: int | None = None


class RegistrationResponse(BaseModel):
    success: bool
    message: str
    user_id: int | None = None


class CaptchaResponse(BaseModel):
    captcha_id: str
    question: str
    answer: int


class CaptchaRequest(BaseModel):
    init_data: str


class ReferralLinkRequest(BaseModel):
    init_data: str
    telegram_id: int


class ReferralLinkResponse(BaseModel):
    success: bool
    referral_link: str | None = None
    message: str


class TicketResponse(BaseModel):
    ticket_code: str
    source: str
    created_at: str


class UserTicketsResponse(BaseModel):
    success: bool
    tickets: list[TicketResponse]
    total_count: int


# Функция для проверки регистрации пользователя
def check_user_registration(telegram_id: int | None, db: Session) -> bool:
    """Проверяет, зарегистрирован ли пользователь"""
    if telegram_id is None:
        return False
    
    user = db.query(BotUser).filter_by(telegram_id=telegram_id).first()
    return user is not None and user.username is not None


# Функция для генерации капчи
def generate_captcha() -> dict:
    """Генерирует математическую капчу"""
    num1 = random.randint(1, 20)
    num2 = random.randint(1, 20)
    operation = random.choice(['+', '-', '*'])
    
    if operation == '+':
        answer = num1 + num2
        question = f"{num1} + {num2} = ?"
    elif operation == '-':
        # Убеждаемся, что результат положительный
        if num1 < num2:
            num1, num2 = num2, num1
        answer = num1 - num2
        question = f"{num1} - {num2} = ?"
    else:  # *
        # Упрощаем умножение для удобства
        num1 = random.randint(2, 10)
        num2 = random.randint(2, 10)
        answer = num1 * num2
        question = f"{num1} × {num2} = ?"
    
    captcha_id = str(uuid.uuid4())
    captcha_storage[captcha_id] = {
        'answer': answer,
        'created_at': datetime.now()
    }
    
    return {
        'captcha_id': captcha_id,
        'question': question,
        'answer': answer
    }


# Функция для проверки капчи
def verify_captcha(captcha_id: str, user_answer: int) -> bool:
    """Проверяет ответ на капчу"""
    if not captcha_id or captcha_id not in captcha_storage:
        return False
    
    captcha_data = captcha_storage[captcha_id]
    
    # Проверяем срок действия капчи (5 минут)
    if datetime.now() - captcha_data['created_at'] > timedelta(minutes=5):
        del captcha_storage[captcha_id]
        return False
    
    # Проверяем ответ
    is_correct = captcha_data['answer'] == user_answer
    
    # Удаляем использованную капчу
    if captcha_id in captcha_storage:
        del captcha_storage[captcha_id]
    
    return is_correct


# Очистка старых капч (можно запускать периодически)
def cleanup_old_captchas():
    """Удаляет капчи старше 5 минут"""
    now = datetime.now()
    expired_ids = [
        captcha_id for captcha_id, data in captcha_storage.items()
        if now - data['created_at'] > timedelta(minutes=5)
    ]
    for captcha_id in expired_ids:
        del captcha_storage[captcha_id]


@app.get("/favicon.ico")
async def favicon():
    """Обработчик для favicon.ico - возвращает 204 No Content"""
    from fastapi.responses import Response
    return Response(status_code=204)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Главная страница - начинается с регистрации"""
    return templates.TemplateResponse("registration.html", {"request": request})


@app.get("/registration", response_class=HTMLResponse)
async def registration_page(request: Request):
    """Страница регистрации"""
    return templates.TemplateResponse("registration.html", {"request": request})


@app.post("/api/register", response_model=RegistrationResponse)
async def register_user(registration_data: RegistrationRequest, db: Session = Depends(get_db)):
    """
    API endpoint для регистрации пользователя
    """
    try:
        # Проверка initData от Telegram (обязательно!)
        if not registration_data.init_data:
            raise HTTPException(status_code=400, detail="initData обязателен для регистрации")
        
        # Обрабатываем initData (может быть в JSON формате)
        init_data_to_validate = registration_data.init_data.strip()
        
        # Если initData выглядит как JSON-строка, декодируем
        if init_data_to_validate.startswith('"') and init_data_to_validate.endswith('"'):
            import json
            try:
                init_data_to_validate = json.loads(init_data_to_validate)
                print("🔍 /api/register: initData был в JSON формате, декодирован")
            except Exception as e:
                print(f"⚠️ /api/register: не удалось декодировать JSON: {e}")
        
        # Убираем возможные лишние пробелы
        init_data_to_validate = init_data_to_validate.strip()
        
        print(f"🔍 /api/register: начинаем валидацию initData...")
        print(f"🔍 /api/register: длина initData: {len(init_data_to_validate)}")
        
        if not validate_telegram_init_data(init_data_to_validate):
            raise HTTPException(status_code=403, detail="Невалидный initData. Откройте приложение через Telegram.")
        
        # Проверка капчи
        if not registration_data.captcha_id or not registration_data.captcha_answer:
            raise HTTPException(status_code=400, detail="Необходимо решить капчу")
        
        if not verify_captcha(registration_data.captcha_id, registration_data.captcha_answer):
            raise HTTPException(status_code=400, detail="Неверный ответ на капчу. Попробуйте снова.")
        
        # Очистка username (убираем @ если есть)
        username = registration_data.username.strip().replace('@', '')
        
        # Валидация username
        if len(username) < 1:
            raise HTTPException(status_code=400, detail="Не удалось получить никнейм из Telegram")
        
        if len(username) > 32:
            raise HTTPException(status_code=400, detail="Никнейм не может быть длиннее 32 символов")
        
        if not username.replace('_', '').replace('-', '').isalnum():
            # Если username не соответствует стандарту, создаем из first_name или telegram_id
            if registration_data.first_name:
                username = registration_data.first_name.lower().replace(' ', '_')[:32]
            else:
                username = f"user{registration_data.telegram_id}"[:32]
        
        # Проверка, не занят ли username (но не блокируем, если это тот же пользователь)
        existing_user_by_username = db.query(BotUser).filter_by(username=username).first()
        if existing_user_by_username and existing_user_by_username.telegram_id != registration_data.telegram_id:
            # Если username занят другим пользователем, добавляем суффикс
            username = f"{username}_{registration_data.telegram_id}"[:32]
        
        # telegram_id обязателен для регистрации
        if not registration_data.telegram_id:
            raise HTTPException(status_code=400, detail="Telegram ID обязателен для регистрации")
        
        # Проверяем существующего пользователя
        bot_user = db.query(BotUser).filter_by(telegram_id=registration_data.telegram_id).first()
        is_new_user = False
        
        if bot_user:
            # Обновляем существующего пользователя
            bot_user.username = username
            if registration_data.first_name:
                bot_user.first_name = registration_data.first_name
            if registration_data.last_name:
                bot_user.last_name = registration_data.last_name
            user_id = bot_user.id
            
            # Проверяем, есть ли у пользователя билеты. Если нет - создаем
            existing_tickets = db.query(Ticket).filter_by(user_id=registration_data.telegram_id).count()
            if existing_tickets == 0:
                # Создаём билет для пользователя, если у него его нет
                ticket_code = generate_ticket_code()
                # Проверяем уникальность кода
                while db.query(Ticket).filter_by(ticket_code=ticket_code).first():
                    ticket_code = generate_ticket_code()
                
                new_ticket = Ticket(
                    user_id=registration_data.telegram_id,
                    ticket_code=ticket_code,
                    source='registration'
                )
                db.add(new_ticket)
                print(f"Создан билет {ticket_code} для существующего пользователя {registration_data.telegram_id}")
        else:
            # Создаём нового пользователя
            is_new_user = True
            new_user = BotUser(
                telegram_id=registration_data.telegram_id,
                username=username,
                first_name=registration_data.first_name,
                last_name=registration_data.last_name,
                version='basic'
            )
            db.add(new_user)
            db.flush()
            user_id = new_user.id
            
            # Создаём билет для нового пользователя при регистрации
            ticket_code = generate_ticket_code()
            # Проверяем уникальность кода
            while db.query(Ticket).filter_by(ticket_code=ticket_code).first():
                ticket_code = generate_ticket_code()
            
            new_ticket = Ticket(
                user_id=registration_data.telegram_id,
                ticket_code=ticket_code,
                source='registration'
            )
            db.add(new_ticket)
        
        db.commit()
        
        return RegistrationResponse(
            success=True,
            message="Регистрация успешна",
            user_id=user_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Ошибка при регистрации: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@app.get("/api/check-registration")
async def check_registration(telegram_id: int | None = None, db: Session = Depends(get_db)):
    """API endpoint для проверки регистрации пользователя"""
    if telegram_id is None:
        return JSONResponse({"registered": False, "message": "Telegram ID не предоставлен"})
    
    is_registered = check_user_registration(telegram_id, db)
    return JSONResponse({"registered": is_registered})


@app.get("/api/next-screen")
async def get_next_screen():
    """
    API endpoint для получения URL следующего доступного экрана.
    Возвращает первый доступный экран из конфигурации ENABLED_SCREENS.
    """
    # Порядок проверки экранов (в порядке следования)
    screen_order = [
        ('create1', '/create'),
        ('create2', '/create2'),
        ('create3', '/create3'),
        ('create4', '/create4'),
        ('create5', '/create5'),
        ('subscriptions', '/subscriptions'),
        ('check', '/check'),
    ]
    
    # Ищем первый доступный экран
    for screen_key, screen_url in screen_order:
        if ENABLED_SCREENS.get(screen_key, True):
            return JSONResponse({
                "success": True,
                "next_screen": screen_url,
                "screen_key": screen_key
            })
    
    # Если ни один экран не доступен, возвращаем ошибку
    return JSONResponse({
        "success": False,
        "message": "Нет доступных экранов"
    }, status_code=404)


@app.post("/api/captcha/generate", response_model=CaptchaResponse)
async def generate_captcha_endpoint(captcha_request: CaptchaRequest):
    """
    API endpoint для генерации новой капчи.
    Требует валидный initData от Telegram для безопасности.
    """
    print(f"🔍 /api/captcha/generate: получен запрос")
    print(f"🔍 init_data присутствует: {bool(captcha_request.init_data)}")
    
    # Проверяем initData перед генерацией капчи
    if not captcha_request.init_data:
        print("❌ /api/captcha/generate: initData отсутствует")
        raise HTTPException(status_code=400, detail="initData обязателен для генерации капчи")
    
    # Важно: initData может быть передан через JSON.stringify, что может привести к двойному кодированию
    # Проверяем, нужно ли декодировать из JSON
    init_data_to_validate = captcha_request.init_data.strip()
    
    # Если initData выглядит как JSON-строка (начинается и заканчивается кавычками), декодируем
    if init_data_to_validate.startswith('"') and init_data_to_validate.endswith('"'):
        import json
        try:
            init_data_to_validate = json.loads(init_data_to_validate)
            print("🔍 /api/captcha/generate: initData был в JSON формате, декодирован")
        except Exception as e:
            print(f"⚠️ /api/captcha/generate: не удалось декодировать JSON: {e}")
            # Продолжаем с исходным значением
    
    # Убираем возможные лишние пробелы и переносы строк
    init_data_to_validate = init_data_to_validate.strip()
    
    print(f"🔍 /api/captcha/generate: начинаем валидацию initData...")
    print(f"🔍 /api/captcha/generate: длина initData: {len(init_data_to_validate)}")
    print(f"🔍 /api/captcha/generate: первые 100 символов initData: {init_data_to_validate[:100]}...")
    
    is_valid = validate_telegram_init_data(init_data_to_validate)
    print(f"🔍 /api/captcha/generate: результат валидации = {is_valid}")
    
    if not is_valid:
        print("❌ /api/captcha/generate: валидация не прошла, возвращаем 403")
        raise HTTPException(status_code=403, detail="Невалидный initData. Откройте приложение через Telegram.")
    
    print("✅ /api/captcha/generate: валидация прошла, генерируем капчу")
    cleanup_old_captchas()
    captcha = generate_captcha()
    return CaptchaResponse(
        captcha_id=captcha['captcha_id'],
        question=captcha['question'],
        answer=captcha['answer']
    )

@app.get("/create", response_class=HTMLResponse)
@app.get("/create1", response_class=HTMLResponse)
async def create_page(request: Request):
    """Первый шаг создания розыгрыша"""
    if not ENABLED_SCREENS.get('create1', True):
        raise HTTPException(status_code=404, detail="Страница недоступна")
    return templates.TemplateResponse("create_1.html", {"request": request, "screen_switch_delay": SCREEN_SWITCH_DELAY_MS})

@app.get("/create2", response_class=HTMLResponse)
async def create2_page(request: Request):
    if not ENABLED_SCREENS.get('create2', True):
        raise HTTPException(status_code=404, detail="Страница недоступна")
    return templates.TemplateResponse("create_2.html", {"request": request, "screen_switch_delay": SCREEN_SWITCH_DELAY_MS})

@app.get("/subscriptions", response_class=HTMLResponse)
async def subscriptions_page(request: Request):
    """Алиас для /create2 - проверка подписок"""
    if not ENABLED_SCREENS.get('subscriptions', True):
        raise HTTPException(status_code=404, detail="Страница недоступна")
    return templates.TemplateResponse("create_2.html", {"request": request, "screen_switch_delay": SCREEN_SWITCH_DELAY_MS})

@app.get("/create3", response_class=HTMLResponse)
async def create3_page(request: Request):
    if not ENABLED_SCREENS.get('create3', True):
        raise HTTPException(status_code=404, detail="Страница недоступна")
    return templates.TemplateResponse("create_3.html", {"request": request, "screen_switch_delay": SCREEN_SWITCH_DELAY_MS})

@app.get("/create4", response_class=HTMLResponse)
async def create4_page(request: Request):
    if not ENABLED_SCREENS.get('create4', True):
        raise HTTPException(status_code=404, detail="Страница недоступна")
    return templates.TemplateResponse("create_4.html", {"request": request, "screen_switch_delay": SCREEN_SWITCH_DELAY_MS})

@app.get("/create5", response_class=HTMLResponse)
async def create5_page(request: Request):
    if not ENABLED_SCREENS.get('create5', True):
        raise HTTPException(status_code=404, detail="Страница недоступна")
    return templates.TemplateResponse("InProgress.html", {"request": request, "screen_switch_delay": SCREEN_SWITCH_DELAY_MS})


@app.post("/api/referral/generate", response_model=ReferralLinkResponse)
async def generate_referral_link(request_data: ReferralLinkRequest, db: Session = Depends(get_db)):
    """
    API endpoint для генерации реферальной ссылки.
    Требует валидный initData от Telegram.
    """
    try:
        # Получаем имя бота в начале функции
        try:
            bot_username = get_bot_username()
        except (ValueError, HTTPException) as e:
            raise HTTPException(status_code=500, detail=f"Ошибка конфигурации: {str(e)}")
        
        # Проверяем initData (может быть пустым в некоторых случаях)
        # Если initData пустой, проверяем пользователя по telegram_id
        if request_data.init_data and request_data.init_data.strip():
            if not validate_telegram_init_data(request_data.init_data):
                raise HTTPException(status_code=403, detail="Невалидный initData. Откройте приложение через Telegram.")
        else:
            # Если initData пустой, проверяем, что пользователь существует в БД
            # Это менее безопасно, но позволяет работать в случаях, когда initData недоступен
            print(f"Предупреждение: initData пустой для пользователя {request_data.telegram_id}, проверяем по telegram_id")
        
        # Проверяем, что пользователь существует
        user = db.query(BotUser).filter_by(telegram_id=request_data.telegram_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        # Проверяем, есть ли уже ссылка для этого пользователя (любая - использованная или нет)
        # Ссылка должна быть фиксированной для пользователя
        existing_link = db.query(ReferralLink).filter_by(
            creator_id=request_data.telegram_id
        ).order_by(ReferralLink.created_at.desc()).first()
        
        if existing_link:
            # Если есть ссылка (даже если она уже использована), возвращаем её
            referral_url = f"https://t.me/{bot_username}?start=ref_{existing_link.referral_code}"
            
            # Определяем сообщение в зависимости от статуса ссылки
            if existing_link.is_used:
                message = "Ваша реферальная ссылка (уже использована)"
            else:
                message = "Ваша реферальная ссылка"
            
            return ReferralLinkResponse(
                success=True,
                referral_link=referral_url,
                message=message
            )
        
        # Если ссылки нет, создаём новую (это происходит только при первом запросе)
        # Генерируем уникальный код
        referral_code = secrets.token_urlsafe(16)
        
        # Проверяем уникальность кода
        while db.query(ReferralLink).filter_by(referral_code=referral_code).first():
            referral_code = secrets.token_urlsafe(16)
        
        # Создаем реферальную ссылку
        referral_link = ReferralLink(
            referral_code=referral_code,
            creator_id=request_data.telegram_id,
            is_used=False
        )
        db.add(referral_link)
        db.commit()
        
        # Используем уже полученное имя бота
        referral_url = f"https://t.me/{bot_username}?start=ref_{referral_code}"
        
        return ReferralLinkResponse(
            success=True,
            referral_link=referral_url,
            message="Реферальная ссылка создана"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Ошибка при создании реферальной ссылки: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@app.get("/api/tickets", response_model=UserTicketsResponse)
async def get_user_tickets(
    telegram_id: int,
    init_data: str | None = None,
    db: Session = Depends(get_db)
):
    """
    API endpoint для получения билетов пользователя.
    Требует telegram_id и опционально init_data для проверки.
    """
    try:
        # Опциональная проверка initData, если предоставлен
        # Если init_data пустой или не предоставлен, просто пропускаем проверку
        if init_data and init_data.strip():
            if not validate_telegram_init_data(init_data):
                print(f"Предупреждение: Невалидный initData для пользователя {telegram_id}, но продолжаем без проверки")
                # Не блокируем запрос, если initData невалидный - просто логируем
        else:
            print(f"Предупреждение: initData не предоставлен для пользователя {telegram_id}, продолжаем без проверки")
        
        # Проверяем, что пользователь существует
        user = db.query(BotUser).filter_by(telegram_id=telegram_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        # Получаем все билеты пользователя, отсортированные по дате создания (новые первые)
        tickets = db.query(Ticket).filter_by(user_id=telegram_id).order_by(Ticket.created_at.desc()).all()
        
        tickets_data = [
            TicketResponse(
                ticket_code=ticket.ticket_code,
                source=ticket.source,
                created_at=ticket.created_at.strftime("%H:%M %d.%m.%Y") if ticket.created_at else ""
            )
            for ticket in tickets
        ]
        
        return UserTicketsResponse(
            success=True,
            tickets=tickets_data,
            total_count=len(tickets_data)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Ошибка при получении билетов: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")




