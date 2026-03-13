"""
Скрипт для добавления билетов существующим пользователям, у которых их нет.
"""

from database.db_session import SessionLocal
from database.models import BotUser, Ticket
import secrets
import string
import sys

# Настройка кодировки UTF-8 для консоли Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

def generate_ticket_code(length=5):
    """Генерирует случайный код билета из заглавных букв и цифр"""
    characters = string.ascii_uppercase + string.digits
    # Исключаем похожие символы (0, O, I, 1)
    characters = characters.replace('0', '').replace('O', '').replace('I', '').replace('1', '')
    return ''.join(secrets.choice(characters) for _ in range(length))

def add_tickets_to_existing_users():
    """Добавляет билеты пользователям, у которых их нет"""
    db = SessionLocal()
    try:
        # Получаем всех пользователей
        users = db.query(BotUser).all()
        print(f"Найдено пользователей: {len(users)}\n")
        
        tickets_added = 0
        
        for user in users:
            # Проверяем, есть ли у пользователя билеты
            existing_tickets = db.query(Ticket).filter_by(user_id=user.telegram_id).all()
            
            if not existing_tickets:
                # Создаём билет для пользователя
                ticket_code = generate_ticket_code()
                # Проверяем уникальность кода
                while db.query(Ticket).filter_by(ticket_code=ticket_code).first():
                    ticket_code = generate_ticket_code()
                
                new_ticket = Ticket(
                    user_id=user.telegram_id,
                    ticket_code=ticket_code,
                    source='registration'
                )
                db.add(new_ticket)
                tickets_added += 1
                print(f"✅ Добавлен билет {ticket_code} пользователю {user.telegram_id} (@{user.username or 'без username'})")
            else:
                print(f"⏭️  Пользователь {user.telegram_id} (@{user.username or 'без username'}) уже имеет {len(existing_tickets)} билет(ов)")
        
        if tickets_added > 0:
            db.commit()
            print(f"\n✅ Успешно добавлено билетов: {tickets_added}")
        else:
            print("\n✅ Все пользователи уже имеют билеты")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("Добавление билетов существующим пользователям...\n")
    add_tickets_to_existing_users()
