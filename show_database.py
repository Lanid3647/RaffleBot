# Скрипт для вывода содержимого базы данных
import sys
import logging
from datetime import datetime

# Отключаем логирование SQLAlchemy для чистого вывода
logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)
logging.getLogger('sqlalchemy.pool').setLevel(logging.ERROR)
logging.getLogger('sqlalchemy.dialects').setLevel(logging.ERROR)
# Отключаем все логи SQLAlchemy
logging.getLogger('sqlalchemy').setLevel(logging.ERROR)

# Настройка кодировки UTF-8 для консоли Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

from database.db_session import engine, SessionLocal
from database.models import BotUser, Channel_tg, Raffle, Ticket, ReferralLink
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Создаем отдельную сессию с отключенным echo для чистого вывода
# (чтобы не влиять на основной engine в db_session.py)
quiet_engine = create_engine(
    engine.url,
    pool_size=2,
    max_overflow=0,
    pool_timeout=30,
    pool_recycle=1800,
    echo=False  # Отключаем SQL-логи
)
QuietSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=quiet_engine)

# ⚠️ ВНИМАНИЕ: Установите в True, чтобы удалить всех пользователей при запуске скрипта
DELETE_ALL_USERS = False


def format_datetime(dt):
    """Форматирует datetime для вывода"""
    if dt is None:
        return "Не указано"
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return str(dt)


def print_separator(char="=", length=80):
    """Печатает разделитель"""
    print(char * length)


def show_bot_users(db):
    """Выводит всех пользователей бота"""
    print_separator()
    print("👤 ПОЛЬЗОВАТЕЛИ БОТА (bot_users)")
    print_separator("-")
    
    users = db.query(BotUser).all()
    
    if not users:
        print("Таблица пуста")
        return
    
    print(f"Всего пользователей: {len(users)}\n")
    
    for i, user in enumerate(users, 1):
        print(f"Пользователь #{i}:")
        print(f"  ID (база): {user.id}")
        print(f"  Telegram ID: {user.telegram_id}")
        print(f"  Username: {user.username or 'Не указан'}")
        print(f"  Имя: {user.first_name or 'Не указано'}")
        print(f"  Фамилия: {user.last_name or 'Не указана'}")
        print(f"  Версия: {user.version}")
        print(f"  Premium до: {format_datetime(user.premium_until)}")
        print(f"  Администратор: {'Да' if user.is_admin else 'Нет'}")
        print(f"  Создан: {format_datetime(user.created_at)}")
        
        # Показываем билеты пользователя
        tickets = db.query(Ticket).filter_by(user_id=user.telegram_id).all()
        if tickets:
            print(f"  Билеты ({len(tickets)}):")
            for ticket in tickets:
                print(f"    - {ticket.ticket_code} (источник: {ticket.source}, создан: {format_datetime(ticket.created_at)})")
        else:
            print(f"  Билеты: нет")
        print()


def show_channels(db):
    """Выводит все каналы"""
    print_separator()
    print("📢 КАНАЛЫ TELEGRAM (channels_tg)")
    print_separator("-")
    
    channels = db.query(Channel_tg).all()
    
    if not channels:
        print("Таблица пуста")
        return
    
    print(f"Всего каналов: {len(channels)}\n")
    
    for i, channel in enumerate(channels, 1):
        print(f"Канал #{i}:")
        print(f"  ID (база): {channel.id}")
        print(f"  Channel ID: {channel.channel_id}")
        print(f"  Название: {channel.channel_name or 'Не указано'}")
        print(f"  Username: {channel.channel_username or 'Не указан'}")
        print(f"  Владелец (ID): {channel.owner_id}")
        print(f"  Активен: {'Да' if channel.is_active else 'Нет'}")
        print(f"  Статус: {channel.status}")
        print(f"  Создан: {format_datetime(channel.created_at)}")
        print()


def show_raffles(db):
    """Выводит все розыгрыши"""
    print_separator()
    print("🎁 РОЗЫГРЫШИ (raffles)")
    print_separator("-")
    
    raffles = db.query(Raffle).all()
    
    if not raffles:
        print("Таблица пуста")
        return
    
    print(f"Всего розыгрышей: {len(raffles)}\n")
    
    for i, raffle in enumerate(raffles, 1):
        print(f"Розыгрыш #{i}:")
        print(f"  ID (база): {raffle.id}")
        print(f"  Название: {raffle.name}")
        print(f"  Владелец (Telegram ID): {raffle.owner_id}")
        print(f"  Тип выбора победителя: {raffle.winner_type}")
        print(f"  Количество победителей: {raffle.winners_count}")
        print(f"  Дата начала: {format_datetime(raffle.start_date)}")
        print(f"  Дата окончания: {format_datetime(raffle.end_date)}")
        print(f"  Статус: {raffle.status}")
        print(f"  Тип медиа: {raffle.media_type or 'Не указан'}")
        print(f"  ID медиа файла: {raffle.media_file_id or 'Не указан'}")
        print(f"  Подпись к медиа: {raffle.media_caption[:100] + '...' if raffle.media_caption and len(raffle.media_caption) > 100 else (raffle.media_caption or 'Не указана')}")
        print(f"  Реферальный бонус включен: {'Да' if raffle.referral_bonus_enable else 'Нет'}")
        if raffle.referral_bonus_enable:
            print(f"    - Билетов за реферала: {raffle.referral_bonus_tickets}")
            print(f"    - Требуется рефералов: {raffle.referral_bonus_required}")
        print(f"  Каналы публикации: {raffle.publication_channels or 'Не указаны'}")
        print(f"  Каналы подписки: {raffle.subscription_channels or 'Не указаны'}")
        print(f"  Усиление удачи: {'Включено' if raffle.luck_boost_enabled else 'Выключено'}")
        print(f"  Капча: {'Включена' if raffle.captcha_enabled else 'Выключена'}")
        print(f"  Создан: {format_datetime(raffle.created_at)}")
        print()


def show_statistics(db):
    """Выводит статистику по базе данных"""
    print_separator()
    print("📊 СТАТИСТИКА")
    print_separator("-")
    
    users_count = db.query(BotUser).count()
    channels_count = db.query(Channel_tg).count()
    raffles_count = db.query(Raffle).count()
    tickets_count = db.query(Ticket).count()
    
    active_channels = db.query(Channel_tg).filter(Channel_tg.is_active == True).count()
    active_raffles = db.query(Raffle).filter(Raffle.status == 'active').count()
    draft_raffles = db.query(Raffle).filter(Raffle.status == 'draft').count()
    
    print(f"Всего пользователей: {users_count}")
    print(f"Всего каналов: {channels_count} (активных: {active_channels})")
    print(f"Всего розыгрышей: {raffles_count}")
    print(f"  - Активных: {active_raffles}")
    print(f"  - Черновиков: {draft_raffles}")
    print(f"Всего билетов: {tickets_count}")
    print()


def main():
    """Основная функция"""
    print_separator()
    print("🗄️  СОДЕРЖИМОЕ БАЗЫ ДАННЫХ")
    print_separator()
    print(f"Время вывода: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    db = QuietSessionLocal()
    try:
        # Удаление всех пользователей, если включено
        if DELETE_ALL_USERS:
            print_separator()
            print("⚠️  УДАЛЕНИЕ ВСЕХ ПОЛЬЗОВАТЕЛЕЙ И ЗАВИСИМЫХ ДАННЫХ")
            print_separator("-")
            users_count = db.query(BotUser).count()
            print(f"Найдено пользователей для удаления: {users_count}")
            
            if users_count > 0:
                deleted_counts = {}
                
                # 1. Удаляем все билеты (связаны через user_id -> telegram_id)
                tickets_count = db.query(Ticket).count()
                if tickets_count > 0:
                    print(f"Удаление всех билетов: {tickets_count}")
                    db.query(Ticket).delete()
                    deleted_counts['tickets'] = tickets_count
                
                # 2. Удаляем все реферальные ссылки (связаны через creator_id и used_by_id -> telegram_id)
                referral_links_count = db.query(ReferralLink).count()
                if referral_links_count > 0:
                    print(f"Удаление всех реферальных ссылок: {referral_links_count}")
                    db.query(ReferralLink).delete()
                    deleted_counts['referral_links'] = referral_links_count
                
                # 3. Удаляем все розыгрыши (связаны через owner_id -> telegram_id)
                raffles_count = db.query(Raffle).count()
                if raffles_count > 0:
                    print(f"Удаление всех розыгрышей: {raffles_count}")
                    db.query(Raffle).delete()
                    deleted_counts['raffles'] = raffles_count
                
                # 4. Удаляем все каналы (связаны через owner_id -> bot_users.id)
                channels_count = db.query(Channel_tg).count()
                if channels_count > 0:
                    print(f"Удаление всех каналов: {channels_count}")
                    db.query(Channel_tg).delete()
                    deleted_counts['channels'] = channels_count
                
                # 5. Удаляем всех пользователей (последними, т.к. на них ссылаются другие таблицы)
                deleted_users = db.query(BotUser).delete()
                deleted_counts['users'] = deleted_users
                
                # Коммитим все изменения
                db.commit()
                
                # Выводим итоговую статистику
                print()
                print("✅ Удаление завершено:")
                print(f"  - Пользователей: {deleted_counts.get('users', 0)}")
                if deleted_counts.get('tickets', 0) > 0:
                    print(f"  - Билетов: {deleted_counts.get('tickets', 0)}")
                if deleted_counts.get('referral_links', 0) > 0:
                    print(f"  - Реферальных ссылок: {deleted_counts.get('referral_links', 0)}")
                if deleted_counts.get('raffles', 0) > 0:
                    print(f"  - Розыгрышей: {deleted_counts.get('raffles', 0)}")
                if deleted_counts.get('channels', 0) > 0:
                    print(f"  - Каналов: {deleted_counts.get('channels', 0)}")
            else:
                print("Пользователей для удаления не найдено")
            print()
        
        # Выводим данные из таблиц
        show_bot_users(db)
        show_channels(db)
        show_raffles(db)
        
        print_separator()
        print("✅ Вывод данных завершен")
        print_separator()
        
    except Exception as e:
        print(f"\n❌ ОШИБКА при работе с базой данных: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
