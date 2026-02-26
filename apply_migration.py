#!/usr/bin/env python3
"""
Скрипт для применения миграций базы данных
Автоматически применяет все необходимые миграции
"""
import sys
import os

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(__file__))

def main():
    """Применяет миграции базы данных"""
    print("=" * 70)
    print("🔄 Применение миграций базы данных")
    print("=" * 70)
    
    try:
        # Импортируем и запускаем миграцию
        from migrations.add_new_fields import migrate
        
        print("\n📋 Применение миграции: add_new_fields.py")
        print("   Добавление полей: channel_messages, winners_selected, completed_at")
        print()
        
        migrate()
        
        print("\n" + "=" * 70)
        print("✅ Миграции успешно применены!")
        print("=" * 70)
        print("\n💡 Теперь можно запустить бота: python start.py")
        
    except Exception as e:
        print(f"\n❌ Ошибка при применении миграций: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
