from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database.models import Raffle
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from datetime import datetime
from database.db_session import get_db
from database.models import Channel_tg, BotUser

load_dotenv()

DATABASE_URL=os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def get_for_type_eight(user_id, selected_channels=None):
    """
    Создает клавиатуру с каналами пользователя для публикации
    selected_channels - список Telegram ID выбранных каналов (channel.channel_id)
    """
    if selected_channels is None:
        selected_channels = []

    print(f"=== DEBUG get_for_type_eight ===")
    print(f"User ID: {user_id}")
    print(f"Selected channels: {selected_channels}")

    db = next(get_db())
    bot_user = db.query(BotUser).filter_by(telegram_id=user_id).first()

    if not bot_user:
        print("Бот пользователь не найден")
        return InlineKeyboardMarkup([[]])

    # Получаем каналы пользователя
    user_channels = db.query(Channel_tg).filter_by(
        owner_id=bot_user.id,
        status='active'
    ).all()

    print(f"Найдено каналов в БД: {len(user_channels)}")

    keyboard = []

    # Определяем отображаемое имя канала
    for channel in user_channels:
        channel_name = channel.channel_name or channel.channel_username or f"Канал {channel.channel_id}"

        # 🔥 ВАЖНОЕ ИЗМЕНЕНИЕ: Используем channel.channel_id (Telegram ID), а не channel.id (базовый ID)
        channel_telegram_id = str(channel.channel_id)

        # Проверяем, выбран ли канал
        # selected_channels должен содержать Telegram ID каналов
        is_selected = channel_telegram_id in selected_channels

        print(f"Канал {channel.channel_id} '{channel_name}': выбран = {is_selected}")

        emoji = "✅" if is_selected else "⚪"

        # 🔥 ВАЖНОЕ ИЗМЕНЕНИЕ: В callback_data сохраняем Telegram ID
        button = InlineKeyboardButton(
            f"{emoji} {channel_name}",
            callback_data=f"select_channel_{channel_telegram_id}"  # Используем channel_id, а не id
        )
        keyboard.append([button])

    # Кнопка "Продолжить"
    if user_channels:  # Показываем кнопку, если есть каналы
        keyboard.append([
            InlineKeyboardButton("➡️ Продолжить", callback_data="continue_to_next_step")
        ])

    print("=== END DEBUG ===")
    return InlineKeyboardMarkup(keyboard)


def get_for_type_nine(user_id, selected_channels=None):
    """
    Создает клавиатуру с каналами пользователя для подписки
    selected_channels - список Telegram ID выбранных каналов (channel.channel_id)
    """
    if selected_channels is None:
        selected_channels = []

    print(f"=== DEBUG get_for_type_nine ===")
    print(f"User ID: {user_id}")
    print(f"Selected channels: {selected_channels}")

    db = next(get_db())
    bot_user = db.query(BotUser).filter_by(telegram_id=user_id).first()

    if not bot_user:
        print("Бот пользователь не найден")
        return InlineKeyboardMarkup([[]])

    # Получаем каналы пользователя
    user_channels = db.query(Channel_tg).filter_by(
        owner_id=bot_user.id,
        status='active'
    ).all()

    print(f"Найдено каналов в БД: {len(user_channels)}")

    keyboard = []

    # Определяем отображаемое имя канала
    for channel in user_channels:
        channel_name = channel.channel_name or channel.channel_username or f"Канал {channel.channel_id}"

        # 🔥 ВАЖНОЕ ИЗМЕНЕНИЕ: Используем channel.channel_id
        channel_telegram_id = str(channel.channel_id)

        # Проверяем, выбран ли канал
        is_selected = channel_telegram_id in selected_channels

        print(f"Канал {channel.channel_id} '{channel_name}': выбран = {is_selected}")

        emoji = "✅" if is_selected else "⚪"

        # 🔥 ВАЖНОЕ ИЗМЕНЕНИЕ: В callback_data сохраняем Telegram ID
        button = InlineKeyboardButton(
            f"{emoji} {channel_name}",
            callback_data=f"select_channel_{channel_telegram_id}"  # Используем channel_id, а не id
        )
        keyboard.append([button])

    # Кнопка "Сохранить"
    if user_channels:  # Показываем кнопку, если есть каналы
        keyboard.append([
            InlineKeyboardButton("➡️ Сохранить", callback_data="continue_to_next_step")
        ])

    print("=== END DEBUG ===")
    return InlineKeyboardMarkup(keyboard)
def get_for_type_ten(user_id, context):  # ✅ БЕЗ self
    """Создает клавиатуру для шага 10"""
    boost_emoji = "✅" if context.user_data.get('luck_boost_enabled') else "⚪"
    captcha_emoji = "✅" if context.user_data.get('captcha_enabled') else "⚪"

    keyboard = [
        [
            InlineKeyboardButton(
                f"{boost_emoji} Буст на удачу",
                callback_data="toggle_boost"
            )
        ],
        [
            InlineKeyboardButton(
                f"{captcha_emoji} Капча",
                callback_data="toggle_captcha"
            )
        ]
    ]

    if context.user_data.get('luck_boost_enabled') or context.user_data.get('captcha_enabled'):
        keyboard.append([
            InlineKeyboardButton("💾 Сохранить", callback_data="save_options")
        ])

    return InlineKeyboardMarkup(keyboard)

# То же самое для get_selected_count
def get_selected_count(context):  # ✅ БЕЗ self
    """Считает сколько опций выбрано"""
    count = 0
    if context.user_data.get('luck_boost_enabled'):
        count += 1
    if context.user_data.get('captcha_enabled'):
        count += 1
    return count


def collect_raffle_data(context):
    """Собирает все данные розыгрыша из context.user_data в единую структуру"""
    from database.db_session import get_db
    from database.models import Channel_tg, BotUser

    # 1. Получаем step_data - здесь ВСЕ основные данные
    step_data = context.user_data.get('step_data', {})

    # 2. Получаем данные из step_data (а не из верхнего уровня context.user_data)
    winner_type = context.user_data.get('step_1', 'auto')
    winners_count = context.user_data.get('step_2', 1)

    # ВСЕ ОСТАЛЬНЫЕ данные берутся из step_data!
    service_name = step_data.get('step_3', 'Без названия')
    start_time = step_data.get('step_4')
    end_time = step_data.get('step_5')
    content_data = step_data.get('step_6', {})
    referral_data = step_data.get('step_7', {})
    publication_channels = step_data.get('step_8', [])  # Telegram ID
    subscription_channels = step_data.get('step_9', [])  # Telegram ID

    # 3. ВАЖНО: Получаем данные из шага 10
    step_10_data = step_data.get('step_10', {})
    luck_boost_enabled = step_10_data.get('luck_boost_enabled', False)
    captcha_enabled = step_10_data.get('captcha_enabled', False)

    # 4. Также проверяем флаги на верхнем уровне (на всякий случай)
    if 'luck_boost_enabled' in context.user_data:
        luck_boost_enabled = context.user_data['luck_boost_enabled']
    if 'captcha_enabled' in context.user_data:
        captcha_enabled = context.user_data['captcha_enabled']

    # 5. Форматируем
    winner_type_text = "Автоматический" if winner_type == 'auto' else "Ручной"

    # Форматируем время
    start_time_text = start_time.strftime("%d.%m.%Y, %H:%M:%S") if start_time else "Не указано"
    end_time_text = end_time.strftime("%d.%m.%Y, %H:%M:%S") if end_time else "Не указано"

    # Реферальные данные
    referral_enabled = referral_data.get('referral_bonus_enable', False)
    referral_required = referral_data.get('referral_bonus_required', 1)
    referral_tickets = referral_data.get('referral_bonus_tickets', 1)

    referral_text = f"{referral_tickets} билет за {referral_required} реферал" if referral_enabled else "Отключено"

    # 🔥 ИСПРАВЛЕНИЕ: Получаем названия каналов по Telegram ID
    db = next(get_db())
    user_id = None

    # 🔥 ИСПРАВЛЕНИЕ: Правильно получаем user_id из context.user_data
    if 'user_data' in locals():
        # Проверяем, есть ли в context.user_data
        user_data = context.user_data
        user_id = user_data.get('user_id')

    # 🔥 АЛЬТЕРНАТИВНО: Если в context.user_data нет user_id, можно получить из update
    # (но в этой функции нет доступа к update)

    publication_channel_names = []
    subscription_channel_names = []

    try:
        # Получаем пользователя
        bot_user = None
        if user_id:
            bot_user = db.query(BotUser).filter_by(telegram_id=user_id).first()

        # Для публикационных каналов
        for channel_telegram_id in publication_channels:
            if bot_user:
                channel = db.query(Channel_tg).filter_by(
                    channel_id=str(channel_telegram_id),
                    owner_id=bot_user.id
                ).first()
            else:
                # Если не найден пользователь, ищем канал только по channel_id
                channel = db.query(Channel_tg).filter_by(channel_id=str(channel_telegram_id)).first()

            if channel:
                name = channel.channel_name or channel.channel_username or f"Канал {channel_telegram_id}"
                publication_channel_names.append(name)
            else:
                publication_channel_names.append(f"Канал {channel_telegram_id}")

        # Для каналов подписки
        for channel_telegram_id in subscription_channels:
            if bot_user:
                channel = db.query(Channel_tg).filter_by(
                    channel_id=str(channel_telegram_id),
                    owner_id=bot_user.id
                ).first()
            else:
                channel = db.query(Channel_tg).filter_by(channel_id=str(channel_telegram_id)).first()

            if channel:
                name = channel.channel_name or channel.channel_username or f"Канал {channel_telegram_id}"
                subscription_channel_names.append(name)
            else:
                subscription_channel_names.append(f"Канал {channel_telegram_id}")
    except Exception as e:
        print(f"Ошибка при получении названий каналов: {e}")
        publication_channel_names = [f"Канал {id}" for id in publication_channels]
        subscription_channel_names = [f"Канал {id}" for id in subscription_channels]

    # ДЕБАГ: выводим для проверки
    print("=" * 50)
    print("ДЕБАГ collect_raffle_data:")
    print(f"Publication channels (Telegram ID): {publication_channels}")
    print(f"Subscription channels (Telegram ID): {subscription_channels}")
    print(f"Publication channel names: {publication_channel_names}")
    print(f"Subscription channel names: {subscription_channel_names}")
    print("=" * 50)

    return {
        'winner_type': winner_type_text,
        'winners_count': winners_count,
        'service_name': service_name,
        'start_time': start_time_text,
        'end_time': end_time_text,
        'referral_text': referral_text,
        'publication_channels': publication_channel_names,
        'subscription_channels': subscription_channel_names,
        'publication_channels_ids': publication_channels,  # 🔥 Сохраняем ID для использования
        'subscription_channels_ids': subscription_channels,  # 🔥 Сохраняем ID для использования
        'luck_boost_enabled': luck_boost_enabled,
        'captcha_enabled': captcha_enabled,
        'step_data': step_data
    }


def generate_confirmation_text(raffle_data, context=None):
    """Генерирует красивый текст подтверждения"""

    text = (
        f"📋 Сводка по розыгрышу:\n\n"

        f"🤖 Тип определения: {raffle_data.get('winner_type', 'Автоматический')}\n"
        f"🏆 Количество победителей: {raffle_data.get('winners_count', 1)}\n"
        f"📝 Название: \"{raffle_data.get('service_name', 'Без названия')}\"\n"
        f"⏰ Начало: {raffle_data.get('start_time', 'Не указано')}\n"
        f"⏰ Окончание: {raffle_data.get('end_time', 'Не указано')}\n"
        f"🎯 Буст на удачу: {'✅ Включен' if raffle_data.get('luck_boost_enabled', False) else '❌ Выключен'}\n"
        f"🔐 Капча: {'✅ Включена' if raffle_data.get('captcha_enabled', False) else '❌ Выключена'}\n\n"

        f"📢 Каналы публикации:\n"
    )

    # Добавляем каналы публикации
    publication_channels = raffle_data.get('publication_channels', [])
    if publication_channels:
        for channel in publication_channels:
            text += f"• {channel}\n"
    else:
        text += "• Не выбрано\n"

    text += f"\n<b>📦 Каналы подписки:</b>\n"

    # Добавляем каналы подписки
    subscription_channels = raffle_data.get('subscription_channels', [])
    if subscription_channels:
        for channel in subscription_channels:
            text += f"• {channel}\n"
    else:
        text += "• Не выбрано\n"

    text += "\n<b>⚠️ Внимательно перепроверьте розыгрыш перед сохранением!</b>"

    return text

def get_channel_names(channel_ids, context):
    """Получает названия каналов по их Telegram ID"""
    if not channel_ids:
        return []

    db = next(get_db())
    channel_names = []

    print(f"=== DEBUG get_channel_names ===")
    print(f"Получены channel_ids: {channel_ids}")
    print(f"Тип channel_ids: {type(channel_ids)}")

    for channel_id in channel_ids:
        # 🔥 ИСПРАВЛЕНИЕ: Ищем по channel_id (Telegram ID), а не id
        channel = db.query(Channel_tg).filter_by(channel_id=str(channel_id)).first()

        if channel:
            channel_name = channel.channel_name or channel.channel_username or f"Канал {channel.channel_id}"
            channel_names.append(channel_name)
            print(f"Найден канал {channel_id}: {channel_name}")
        else:
            channel_names.append(f"Канал {channel_id}")
            print(f"Канал {channel_id} не найден в БД")

    print(f"Результат: {channel_names}")
    print("=== END DEBUG ===")
    return channel_names


def get_final_confirmation_keyboard(luck_boost_enabled=False, captcha_enabled=False):
    """Создает интерактивную клавиатуру для финального подтверждения"""
    # Определяем эмодзи и текст для буста и капчи
    boost_emoji = "✅" if luck_boost_enabled else "❌"
    captcha_emoji = "✅" if captcha_enabled else "❌"
    keyboard = [
        [InlineKeyboardButton("🚀 Сохранить розыгрыш", callback_data="save_raffle")],

    ]
    return InlineKeyboardMarkup(keyboard)