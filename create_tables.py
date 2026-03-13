# создаем таблицы в базе данных

from database.models import Base
from database.db_session import engine

def create_tables(): # функция для создания всех таблиц
    Base.metadata.create_all(bind=engine)
    print("все таблицы созданы")

if __name__ == "__main__": # "Если этот файл запущен напрямую (а не импортирован)"
    create_tables() # "Тогда выполни функцию create_tables"


# далее необходимо запустить этот файл в терминале
# python create_tables.py
# проверить что таблицы созданы
# psql -U bot_user -d raffle_bot -W
# и в консоле PostgreSQL
# \dt