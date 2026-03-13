# debug_db.py
import sys
import os

sys.path.append('.')

print("🔍 ДЕБАГ БАЗЫ ДАННЫХ")
print("=" * 60)

# 1. Проверяем подключение напрямую
import psycopg2

print("\n1. Тест прямого подключения через psycopg2:")
try:
    conn = psycopg2.connect(
        "postgresql://postgres:Fynza3-gocnyw-xurzed@db.osvztgewhvuswokqxlyu.supabase.co:5432/postgres?sslmode=require"
    )
    cursor = conn.cursor()
    cursor.execute("SELECT current_user, current_database()")
    user, db = cursor.fetchone()
    print(f"   ✅ Подключено: {db} как {user}")
    conn.close()
except Exception as e:
    print(f"   ❌ Ошибка: {e}")

# 2. Проверяем SQLAlchemy
print("\n2. Тест SQLAlchemy:")
try:
    from database.db_session import engine, SessionLocal

    db = SessionLocal()
    from sqlalchemy import text

    result = db.execute(text("SELECT 'SQLAlchemy работает'"))
    print(f"   ✅ {result.fetchone()[0]}")
    db.close()
except Exception as e:
    print(f"   ❌ Ошибка SQLAlchemy: {e}")

# 3. Проверяем модели
print("\n3. Тест импорта моделей:")
try:
    from database.models import BotUser

    print(f"   ✅ Модель BotUser загружена")
    print(f"   Поля: {[col.name for col in BotUser.__table__.columns]}")
except Exception as e:
    print(f"   ❌ Ошибка моделей: {e}")

# 4. Тест создания/чтения пользователя
print("\n4. Тест работы с данными:")
try:
    from database.db_session import SessionLocal
    from database.models import BotUser

    db = SessionLocal()

    # Считаем пользователей
    count = db.query(BotUser).count()
    print(f"   👤 Пользователей в базе: {count}")

    # Создаем тестового пользователя
    test_user = BotUser(
        telegram_id=777888999,
        username="debug_user",
        first_name="Debug"
    )
    db.add(test_user)
    db.commit()
    print("   ✅ Тестовый пользователь создан")

    # Читаем его обратно
    user = db.query(BotUser).filter_by(telegram_id=777888999).first()
    print(f"   📖 Прочитан: {user.first_name}")

    # Удаляем
    db.delete(user)
    db.commit()
    print("   🗑️ Тестовый пользователь удален")

    db.close()

except Exception as e:
    print(f"   ❌ Ошибка данных: {e}")
    import traceback

    traceback.print_exc()

print("\n" + "=" * 60)
print("📊 РЕЗУЛЬТАТ:")
print("-" * 30)