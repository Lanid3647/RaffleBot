from database.models import Base
from database.db_session import engine

# Удаляем все таблицы
Base.metadata.drop_all(bind=engine)
print("🗑️ Старые таблицы удалены")

# Создаем новые таблицы с правильными типами
Base.metadata.create_all(bind=engine)
print("✅ Новые таблицы созданы с BigInteger для telegram_id"