"""
Скрипт миграции для добавления новых полей в таблицу raffles
"""
from database.db_session import engine, Base
from database.models import Raffle, Participant
from sqlalchemy import text

def migrate():
    """Добавляет новые поля в таблицу raffles"""
    try:
        with engine.begin() as conn:  # Используем begin() для автоматического коммита
            # Проверяем существование полей
            check_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'raffles' AND column_name IN ('channel_messages', 'winners_selected', 'completed_at')
            """)
            result = conn.execute(check_query)
            existing_columns = [row[0] for row in result]
            
            print(f"📋 Найдено существующих полей: {len(existing_columns)}")
            
            # Добавляем channel_messages если его нет
            if 'channel_messages' not in existing_columns:
                conn.execute(text("""
                    ALTER TABLE raffles 
                    ADD COLUMN channel_messages TEXT
                """))
                print("✅ Добавлено поле channel_messages")
            else:
                print("ℹ️  Поле channel_messages уже существует")
            
            # Добавляем winners_selected если его нет
            if 'winners_selected' not in existing_columns:
                conn.execute(text("""
                    ALTER TABLE raffles 
                    ADD COLUMN winners_selected BOOLEAN DEFAULT FALSE
                """))
                print("✅ Добавлено поле winners_selected")
            else:
                print("ℹ️  Поле winners_selected уже существует")
            
            # Добавляем completed_at если его нет
            if 'completed_at' not in existing_columns:
                conn.execute(text("""
                    ALTER TABLE raffles 
                    ADD COLUMN completed_at TIMESTAMP
                """))
                print("✅ Добавлено поле completed_at")
            else:
                print("ℹ️  Поле completed_at уже существует")
            
            # Коммит происходит автоматически при выходе из with engine.begin()
            print("\n✅ Миграция завершена успешно")
            
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    migrate()
