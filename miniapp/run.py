import uvicorn
import os
import sys
import threading
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Переменная для задержки переключения между экранами веб-приложения (в миллисекундах)
SCREEN_SWITCH_DELAY_MS = 1000  # Задержка переключения экранов в миллисекундах (по умолчанию 3 секунды)

# ============================================================================
# КОНФИГУРАЦИЯ ДОСТУПНЫХ ЭКРАНОВ
# ============================================================================
# Установите True для экранов, которые должны быть доступны пользователям
# Установите False для экранов, которые должны быть скрыты (вернет 404)
#
# Пример использования:
#   Чтобы скрыть экраны create3 и create4, установите:
#     'create3': False,
#     'create4': False,
#
#   Чтобы показать только регистрацию и финальный экран:
#     'registration': True,
#     'create1': False,
#     'create2': False,
#     'create3': False,
#     'create4': False,
#     'create5': True,
# ============================================================================
ENABLED_SCREENS = {
    'registration': True,    # / и /registration - страница регистрации
    'create1': False,         # /create и /create1 - первый шаг создания розыгрыша
    'create2': False,         # /create2 - второй шаг (проверка подписок)
    'create3': False,         # /create3 - третий шаг
    'create4': False,         # /create4 - четвертый шаг
    'create5': True,        # /create5 - пятый шаг (InProgress.html)
    'subscriptions': False,   # /subscriptions - алиас для /create2
    'check': False,          # /check - страница проверки (если есть)
}

# Добавляем текущую директорию в путь для импорта
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# Добавляем текущую директорию и родительскую в sys.path
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

def run_bot():
    """Запускает Telegram бота в отдельном потоке"""
    try:
        # Импортируем функцию bot из корневого bot.py
        sys.path.insert(0, parent_dir)
        print("Импорт модуля bot...")
        from bot import bot
        print("✅ Модуль bot успешно импортирован")
        print("\n🤖 Запуск Telegram бота...")
        bot()
    except SystemExit as e:
        # Игнорируем SystemExit, чтобы не прерывать основной поток
        if e.code != 0:
            print(f"\n⚠️  Бот завершился с кодом {e.code}")
    except Exception as e:
        print(f"\n❌ Ошибка при запуске бота: {e}")
        import traceback
        traceback.print_exc()

def run_web_server():
    """Запускает веб-сервер FastAPI"""
    # Меняем рабочую директорию на текущую для правильного поиска модулей
    original_dir = os.getcwd()
    try:
        os.chdir(current_dir)
        
        # Проверяем, что модуль app можно импортировать
        print("Проверка импорта модуля app...")
        try:
            import app
            print("✅ Модуль app успешно импортирован")
            if not hasattr(app, 'app'):
                print("❌ ОШИБКА: В модуле app не найден объект app")
                return
        except SystemExit as e:
            print(f"⚠️  Модуль app вызвал SystemExit с кодом {e.code}")
            print("Попытка запуска без предварительной проверки...")
        except Exception as e:
            print(f"⚠️  Ошибка при импорте модуля app: {e}")
            print("Попытка запуска через uvicorn напрямую...")
        
        # Запускаем uvicorn - он сам импортирует модуль
        uvicorn.run(
            "app:app",  # Строка импорта для поддержки reload
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
            
    except SystemExit as e:
        # Игнорируем SystemExit от uvicorn или других модулей, но не завершаем программу
        if e.code != 0:
            print(f"⚠️  Веб-сервер завершился с кодом {e.code}")
            print("Веб-сервер остановлен, но бот продолжает работать")
    except KeyboardInterrupt:
        print("\n⏹️  Веб-сервер остановлен пользователем")
        raise
    except ImportError as e:
        print(f"❌ Ошибка импорта модуля app: {e}")
        import traceback
        traceback.print_exc()
        print("\nПроверьте:")
        print("1. Установлены ли все зависимости (pip install -r requirements.txt)")
        print("2. Правильно ли настроена база данных")
        print("3. Находитесь ли вы в правильной директории")
    except Exception as e:
        print(f"❌ Ошибка при запуске веб-сервера: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Возвращаемся в исходную директорию
        try:
            os.chdir(original_dir)
        except:
            pass

if __name__ == "__main__":
    try:
        print("=" * 60)
        print("🚀 Запуск приложения...")
        print("=" * 60)
        
        # Запускаем бота в отдельном потоке
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        
        # Небольшая задержка, чтобы бот успел инициализироваться
        import time
        # Используем фиксированную задержку для инициализации бота (не связана с переключением экранов)
        time.sleep(2)
        
        print("\n" + "=" * 60)
        print("🌐 Запуск веб-сервера FastAPI...")
        print(f"📁 Рабочая директория: {current_dir}")
        print("🌐 Сервер будет доступен по адресу: http://localhost:8000")
        print("\n💡 Для доступа извне через ngrok запустите в отдельном терминале:")
        print("   ngrok.exe http 8000")
        print("   (Убедитесь, что веб-сервер запущен перед запуском ngrok!)")
        print("=" * 60 + "\n")
        
        run_web_server()
        
    except SystemExit as e:
        # Не завершаем программу при SystemExit, только логируем
        if e.code != 0:
            print(f"\n⚠️  Приложение завершилось с кодом {e.code}")
        print("Программа продолжает работу...")
    except KeyboardInterrupt:
        print("\n\n⏹️  Остановка серверов...")
        print("Бот и веб-сервер остановлены")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()