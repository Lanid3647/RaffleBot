#!/usr/bin/env python3
"""
Универсальный скрипт запуска Telegram Raffle Bot
Запускает Telegram бота (основной компонент) и опционально веб-сервер мини-приложения
Мини-приложение используется только для участия в розыгрышах, основная работа через текстовый интерфейс бота
"""
import os
import sys
import threading
import time
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def check_env_file():
    """Проверяет наличие и корректность .env файла"""
    required_vars = ['BOT_TOKEN', 'DATABASE_URL']
    missing_vars = []

    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print("❌ ОШИБКА: Отсутствуют обязательные переменные окружения:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n💡 Создайте файл .env в корне проекта и добавьте необходимые переменные.")
        print("   Пример содержимого .env:")
        print("   BOT_TOKEN=your_bot_token_here")
        print("   DATABASE_URL=postgresql://user:password@localhost:5432/raffle_bot")
        print("   BOT_USERNAME=your_bot_username")
        print("   WEBAPP_URL=https://your-webapp-url.com")
        return False

    return True

def check_migrations():
    """Проверяет, применены ли миграции базы данных"""
    try:
        from database.db_session import get_db
        from database.models import Raffle
        from sqlalchemy import inspect

        db = next(get_db())
        try:
            # Проверяем наличие новых полей
            inspector = inspect(db.bind)
            columns = [col['name'] for col in inspector.get_columns('raffles')]

            required_fields = ['channel_messages', 'winners_selected', 'completed_at']
            missing_fields = [field for field in required_fields if field not in columns]

            if missing_fields:
                print("\n⚠️  ВНИМАНИЕ: В базе данных отсутствуют новые поля:")
                for field in missing_fields:
                    print(f"   - {field}")
                print("\n💡 Примените миграции перед запуском:")
                print("   python apply_migration.py")
                print("\n   Или вручную:")
                print("   python migrations/add_new_fields.py")
                return False

            return True
        finally:
            db.close()
    except Exception as e:
        print(f"\n⚠️  Не удалось проверить миграции: {e}")
        print("   Продолжаем запуск, но возможны ошибки...")
        return True  # Продолжаем, чтобы не блокировать запуск

def run_bot():
    """Запускает Telegram бота в отдельном потоке"""
    try:
        print("🤖 Инициализация Telegram бота...")
        from bot import bot
        print("✅ Модуль bot успешно импортирован")
        print("\n🤖 Запуск Telegram бота...")
        bot()
    except SystemExit as e:
        if e.code != 0:
            print(f"\n⚠️  Бот завершился с кодом {e.code}")
    except KeyboardInterrupt:
        print("\n⏹️  Бот остановлен пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка при запуске бота: {e}")
        import traceback
        traceback.print_exc()

def run_web_server():
    """Запускает веб-сервер FastAPI для мини-приложения"""
    try:
        import uvicorn
        
        # Меняем рабочую директорию на miniapp для правильного импорта
        original_dir = os.getcwd()
        miniapp_dir = os.path.join(os.path.dirname(__file__), 'miniapp')
        
        # Проверяем существование директории miniapp
        if not os.path.exists(miniapp_dir):
            print(f"❌ ОШИБКА: Директория {miniapp_dir} не найдена")
            return
        
        # Проверяем наличие файла app.py
        app_file = os.path.join(miniapp_dir, 'app.py')
        if not os.path.exists(app_file):
            print(f"❌ ОШИБКА: Файл {app_file} не найден")
            return
        
        try:
            os.chdir(miniapp_dir)
            
            print("🌐 Запуск веб-сервера FastAPI...")
            print(f"📁 Рабочая директория: {miniapp_dir}")
            
            # Добавляем путь к miniapp в sys.path для импорта
            if miniapp_dir not in sys.path:
                sys.path.insert(0, miniapp_dir)
            
            uvicorn.run(
                "app:app",
                host="0.0.0.0",
                port=8000,
                reload=False,  # Отключаем reload для стабильности
                log_level="info",
                app_dir=miniapp_dir  # Указываем директорию приложения
            )
        finally:
            os.chdir(original_dir)
            
    except KeyboardInterrupt:
        print("\n⏹️  Веб-сервер остановлен пользователем")
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("\n💡 Убедитесь, что установлены все зависимости:")
        print("   pip install -r requirements.txt")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"❌ Ошибка при запуске веб-сервера: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Главная функция запуска"""
    print("=" * 70)
    print("🚀 Telegram Raffle Bot - Запуск приложения")
    print("=" * 70)
    
    # Проверяем наличие .env файла
    if not check_env_file():
        sys.exit(1)
    
    # Проверяем наличие BOT_TOKEN
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token or (bot_token == 'your_bot_token_here'):
        print("⚠️  ВНИМАНИЕ: BOT_TOKEN не настроен или имеет значение по умолчанию")
        print("    Установите правильный токен в файле .env")
        response = input("\n   Продолжить запуск? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)

    # Проверяем миграции
    if not check_migrations():
        response = input("\n   Продолжить запуск без миграций? (y/n): ")
        if response.lower() != 'y':
            print("\n💡 Примените миграции и запустите снова:")
            print("   python apply_migration.py")
            sys.exit(1)

    print("\n✅ Проверка конфигурации пройдена")
    print("\n📋 Компоненты для запуска:")
    print("   1. Telegram бот (основной компонент - текстовый интерфейс)")
    print("   2. Веб-сервер мини-приложения (опционально, только для участия в розыгрышах)")
    print("\n" + "=" * 70)
    
    # Спрашиваем, нужно ли запускать мини-приложение
    webapp_url = os.getenv('WEBAPP_URL', '')
    if webapp_url:
        print("\n💡 Обнаружен WEBAPP_URL в .env")
        # По умолчанию запускаем веб-сервер, если URL настроен
        run_webapp = True
    else:
        print("\n💡 WEBAPP_URL не настроен в .env")
        print("   Мини-приложение будет пропущено (бот работает полностью через текстовый интерфейс)")
        run_webapp = False
    
    print("\n" + "=" * 70)
    print("🤖 Запуск Telegram бота...")
    print("=" * 70)
    print("💬 Бот работает через текстовый интерфейс")
    print("   Пользователи взаимодействуют с ботом через команды и кнопки")
    print("   Мини-приложение используется только для участия в розыгрышах")
    print("=" * 70 + "\n")
    
    if run_webapp:
        # Запускаем бота в отдельном потоке
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()

        # Небольшая задержка для инициализации бота
        print("⏳ Ожидание инициализации бота...")
        time.sleep(3)

        print("\n" + "=" * 70)
        print("🌐 Запуск веб-сервера мини-приложения...")
        print("📡 Сервер будет доступен по адресу: http://localhost:8000")
        print("\n💡 Для доступа извне через ngrok:")
        print("   1. Убедитесь, что веб-сервер запущен")
        print("   2. В отдельном терминале выполните: ngrok http 8000")
        print("   3. Скопируйте HTTPS URL и обновите WEBAPP_URL в .env")
        print("=" * 70 + "\n")

        try:
            # Запускаем веб-сервер в основном потоке
            run_web_server()
        except KeyboardInterrupt:
            print("\n\n" + "=" * 70)
            print("⏹️  Остановка всех сервисов...")
            print("=" * 70)
            print("✅ Бот и веб-сервер остановлены")
            print("=" * 70)
    else:
        # Запускаем только бота в основном потоке
        try:
            run_bot()
        except KeyboardInterrupt:
            print("\n\n" + "=" * 70)
            print("⏹️  Остановка бота...")
            print("=" * 70)
            print("✅ Бот остановлен")
            print("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Принудительная остановка...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)