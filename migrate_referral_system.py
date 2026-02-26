"""
Скрипт миграции для добавления реферальной системы.
Добавляет столбец referral_tickets в таблицу bot_users и создает таблицу referral_links.
"""

from database.db_session import engine
from sqlalchemy import text
import sys

def migrate_referral_system():
    """Выполняет миграцию для реферальной системы"""
    try:
        with engine.connect() as conn:
            # Начинаем транзакцию
            trans = conn.begin()
            
            try:
                # Проверяем, существует ли столбец referral_tickets
                check_column = text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='bot_users' AND column_name='referral_tickets'
                """)
                result = conn.execute(check_column)
                
                if result.fetchone() is None:
                    # Добавляем столбец referral_tickets
                    print("Добавление столбца referral_tickets в таблицу bot_users...")
                    add_column = text("""
                        ALTER TABLE bot_users 
                        ADD COLUMN referral_tickets INTEGER DEFAULT 0
                    """)
                    conn.execute(add_column)
                    print("[OK] Столбец referral_tickets добавлен")
                else:
                    print("[INFO] Столбец referral_tickets уже существует")
                
                # Проверяем, существует ли таблица referral_links
                check_table = text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_name='referral_links'
                """)
                result = conn.execute(check_table)
                
                if result.fetchone() is None:
                    # Создаем таблицу referral_links
                    print("Создание таблицы referral_links...")
                    create_table = text("""
                        CREATE TABLE referral_links (
                            id SERIAL PRIMARY KEY,
                            referral_code VARCHAR(100) UNIQUE NOT NULL,
                            creator_id BIGINT NOT NULL,
                            used_by_id BIGINT,
                            is_used BOOLEAN DEFAULT FALSE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            used_at TIMESTAMP,
                            FOREIGN KEY (creator_id) REFERENCES bot_users(telegram_id),
                            FOREIGN KEY (used_by_id) REFERENCES bot_users(telegram_id)
                        )
                    """)
                    conn.execute(create_table)
                    
                    # Создаем индексы для оптимизации
                    create_index1 = text("""
                        CREATE INDEX idx_referral_links_code ON referral_links(referral_code)
                    """)
                    conn.execute(create_index1)
                    
                    create_index2 = text("""
                        CREATE INDEX idx_referral_links_creator ON referral_links(creator_id)
                    """)
                    conn.execute(create_index2)
                    
                    create_index3 = text("""
                        CREATE INDEX idx_referral_links_used ON referral_links(is_used)
                    """)
                    conn.execute(create_index3)
                    
                    print("[OK] Таблица referral_links создана с индексами")
                else:
                    print("[INFO] Таблица referral_links уже существует")
                
                # Коммитим транзакцию
                trans.commit()
                print("\n[OK] Миграция успешно завершена!")
                
            except Exception as e:
                # Откатываем транзакцию в случае ошибки
                trans.rollback()
                print(f"\n[ERROR] Ошибка при выполнении миграции: {e}")
                import traceback
                traceback.print_exc()
                sys.exit(1)
                
    except Exception as e:
        print(f"\n[ERROR] Ошибка подключения к базе данных: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    import sys
    import io
    # Настройка кодировки UTF-8 для консоли Windows
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except:
            pass
    
    print("=" * 60)
    print("Запуск миграции реферальной системы...")
    print("=" * 60)
    migrate_referral_system()
    print("=" * 60)
