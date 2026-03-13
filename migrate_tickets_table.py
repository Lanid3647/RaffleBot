"""
Скрипт миграции для создания таблицы tickets.
"""

from database.db_session import engine
from sqlalchemy import text
import sys

def migrate_tickets_table():
    """Выполняет миграцию для таблицы tickets"""
    try:
        with engine.connect() as conn:
            # Начинаем транзакцию
            trans = conn.begin()
            
            try:
                # Проверяем, существует ли таблица tickets
                check_table = text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_name='tickets'
                """)
                result = conn.execute(check_table)
                
                if result.fetchone() is None:
                    # Создаем таблицу tickets
                    print("Создание таблицы tickets...")
                    create_table = text("""
                        CREATE TABLE tickets (
                            id SERIAL PRIMARY KEY,
                            user_id BIGINT NOT NULL,
                            ticket_code VARCHAR(20) UNIQUE NOT NULL,
                            source VARCHAR(50) DEFAULT 'registration',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            CONSTRAINT fk_tickets_user FOREIGN KEY (user_id) 
                                REFERENCES bot_users(telegram_id) ON DELETE CASCADE
                        )
                    """)
                    conn.execute(create_table)
                    print("[OK] Таблица tickets создана")
                    
                    # Создаем индексы
                    print("Создание индексов для таблицы tickets...")
                    create_index_user = text("""
                        CREATE INDEX idx_tickets_user_id ON tickets(user_id)
                    """)
                    conn.execute(create_index_user)
                    
                    create_index_code = text("""
                        CREATE INDEX idx_tickets_code ON tickets(ticket_code)
                    """)
                    conn.execute(create_index_code)
                    
                    create_index_created = text("""
                        CREATE INDEX idx_tickets_created_at ON tickets(created_at DESC)
                    """)
                    conn.execute(create_index_created)
                    print("[OK] Индексы созданы")
                else:
                    print("[INFO] Таблица tickets уже существует")
                
                # Коммитим транзакцию
                trans.commit()
                print("[OK] Миграция успешно завершена")
                
            except Exception as e:
                trans.rollback()
                print(f"[ERROR] Ошибка при выполнении миграции: {e}")
                import traceback
                traceback.print_exc()
                sys.exit(1)
                
    except Exception as e:
        print(f"[ERROR] Ошибка подключения к базе данных: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    print("Запуск миграции для таблицы tickets...")
    migrate_tickets_table()
