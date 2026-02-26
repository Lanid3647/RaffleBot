import os
import sys
import logging

# Настройка кодировки UTF-8 для консоли Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler
from dotenv import load_dotenv
from handlers.start import start_command
from handlers.handlers_message import cancel
from handlers.handlers_message import handle_message
from handlers.handlers_keyboards import STEP_2, STEP_3, STEP_4, STEP_9, STEP_5, STEP_6, STEP_7, STEP_8, STEP_10, STEP_1, STEP_11, RaffleCreator, new_version, add_channel_command
#handle_webapp_callback
from telegram.ext import ContextTypes, ConversationHandler
from telegram import Update
from datetime import datetime
from handlers.channel_handlers_keyboards import (my_channels, STEP_CHANNEL_1, tg_channels, back_channel, MAIN_STATE)
from handlers.my_raffles_keyboard import my_raffles_start, handle_raffle_selection, STEP_RAFFLES_1, STEP_RAFFLES_2, handle_raffle_actions, handle_edit_choice, handle_edit_input, STEP_EDIT_1, STEP_EDIT_2, STEP_DELETE_CONFIRM
from handlers.admin_panel import get_admin_handler
#from miniapp.handle_webapp.start import start_command
#from miniapp.handle_webapp.handler import handle_webapp_data
from telegram.ext import CallbackQueryHandler
from telegram.ext import ApplicationBuilder

load_dotenv()

# В начале файла добавьте импорт:
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup
import json

def bot():
    logger.info("Запуск функции bot()")
    # Проверяем наличие токена
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        error_msg = "ОШИБКА: BOT_TOKEN не найден в переменных окружения!"
        logger.error(error_msg)
        print(error_msg)
        print("Создайте файл .env в корне проекта и добавьте строку:")
        print("BOT_TOKEN=ваш_токен_бота")
        return
    
    logger.info(f"Токен бота загружен (длина: {len(bot_token)} символов)")
    print(f"Токен бота загружен (длина: {len(bot_token)} символов)")
    
    try:
        # Создаем приложение
        logger.info("Создание приложения бота...")
        application = ApplicationBuilder().token(bot_token).build()
        logger.info("Приложение бота создано успешно")
        print("✅ Приложение бота создано успешно")
    except Exception as e:
        error_msg = f"Ошибка при создании приложения бота: {e}"
        logger.error(error_msg, exc_info=True)
        print(error_msg)
        import traceback
        traceback.print_exc()
        return

    logger.info("Регистрация обработчиков команд...")
    print("Регистрация обработчиков команд...")
    
    # Добавляем универсальный обработчик для отладки всех команд
    async def debug_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.debug(f"Получена команда: {update.message.text if update.message else 'N/A'}")
        logger.debug(f"Пользователь: {update.effective_user.id if update.effective_user else 'N/A'}")
    
    # Регистрируем обработчики команд с высоким приоритетом
    try:
        application.add_handler(CommandHandler("start", start_command), group=1)
        logger.info("Обработчик /start зарегистрирован (group=1)")
        print("✅ Обработчик /start зарегистрирован (group=1)")
        application.add_handler(CommandHandler("cancel", cancel), group=1)
        logger.info("Обработчик /cancel зарегистрирован (group=1)")
        print("✅ Обработчик /cancel зарегистрирован (group=1)")
    except Exception as e:
        logger.error(f"Ошибка при регистрации обработчиков команд: {e}", exc_info=True)
        raise
    
    # Добавляем обработчик для всех остальных команд для отладки
    async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        command = update.message.text.split()[0] if update.message and update.message.text else "unknown"
        logger.warning(f"Неизвестная команда: {command}")
        await update.message.reply_text(
            "❓ Неизвестная команда. Используйте кнопки меню.",
            parse_mode='HTML'
        )
    
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command), group=1)

#    app.add_handler(CallbackQueryHandler(handle_webapp_callback, pattern=r"^open_webapp:"))



    raffle_creator = RaffleCreator()
    
    # Обработчик для кнопки "Создать розыгрыш" из дашборда
    async def handle_create_raffle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает нажатие на кнопку 'Создать розыгрыш' из дашборда"""
        query = update.callback_query
        await query.answer()
        
        # Используем query.message напрямую, но создаем update с message вместо callback_query
        # query.message уже имеет связь с ботом, просто используем его напрямую
        original_message = query.message
        
        # Создаем новое сообщение на основе оригинального, но с измененным текстом
        # Используем метод copy или создаем новое с теми же параметрами
        from telegram import Message
        
        # Создаем сообщение с правильной связью с ботом
        # Используем bot из original_message, если он есть, иначе из context
        bot_instance = getattr(original_message, 'bot', None) or context.bot
        
        # Создаем сообщение через de_json для правильной инициализации
        message_dict = {
            'message_id': original_message.message_id,
            'date': int(original_message.date.timestamp()),
            'chat': original_message.chat.to_dict(),
            'text': "Создать розыгрыш 🎁",
            'from': query.from_user.to_dict() if query.from_user else None
        }
        
        fake_message = Message.de_json(message_dict, bot=bot_instance)
        
        fake_update = Update(
            update_id=update.update_id,
            message=fake_message
        )
        return await raffle_creator.start(fake_update, context)
    
    draw_conv_handler=ConversationHandler(
        entry_points=[
            MessageHandler(filters.TEXT & filters.Regex("^Создать розыгрыш 🎁$"), raffle_creator.start),
            CallbackQueryHandler(handle_create_raffle_callback, pattern="^start_create_raffle$"),
        ],
        states={
            STEP_1: [
                CallbackQueryHandler(raffle_creator.handle_input, pattern="^(type_auto|type_me)$"),
            ],
            STEP_2: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, raffle_creator.handle_input),
            ],
            STEP_3: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, raffle_creator.handle_input),
            ],
            STEP_4: [
                CallbackQueryHandler(raffle_creator.handle_input, pattern="^(time_start|time_end)$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, raffle_creator.handle_input),
            ],
            STEP_5: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, raffle_creator.handle_input),
            ],
            STEP_6: [
                MessageHandler(filters.ALL, raffle_creator.handle_step_6),
            ],
            STEP_7: [
                CallbackQueryHandler(raffle_creator.handle_input, pattern="^referral_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, raffle_creator.handle_input)
                ],
            STEP_8: [
                CallbackQueryHandler(raffle_creator.handle_input, pattern="^select_channel_"),
                CallbackQueryHandler(raffle_creator.handle_input, pattern="^continue_to_next_step$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND,raffle_creator.handle_input),
            ],
            STEP_9: [
                CallbackQueryHandler(raffle_creator.handle_input, pattern="^select_channel_"),
                CallbackQueryHandler(raffle_creator.handle_input, pattern="^continue_to_next_step$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, raffle_creator.handle_input),
            ],
            STEP_10: [
                CallbackQueryHandler(raffle_creator.handle_input,
                                     pattern="^(toggle_boost|toggle_captcha|save_options)$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, raffle_creator.handle_input),
            ],
            STEP_11: [
                CallbackQueryHandler(raffle_creator.handle_input, pattern="^(luck_boost|captcha|save_raffle)$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, raffle_creator.handle_input),
            ],
        },
        fallbacks=[
            CommandHandler("start", start_command),
            CommandHandler("cancel", cancel),
            MessageHandler(filters.TEXT & filters.Regex("^(❌Отменить создание|/cancel)$"), raffle_creator.cancel),
        ],
        map_to_parent={
            ConversationHandler.END: MAIN_STATE
        },
    )


    # ConversationHandler должен быть в группе 2, чтобы команды обрабатывались первыми
    application.add_handler(draw_conv_handler, group=2)
    
    # Обработчик "Мои розыгрыши"
    draw_channels_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.TEXT & filters.Regex("^Мои розыгрыши 🗒$"), my_raffles_start)
        ],
        states={
            STEP_RAFFLES_1: [
                CallbackQueryHandler(handle_raffle_selection)
            ],
            STEP_RAFFLES_2: [
                CallbackQueryHandler(handle_raffle_actions)
            ],
            STEP_EDIT_1: [
                CallbackQueryHandler(handle_edit_choice)
            ],
            STEP_EDIT_2: [
                MessageHandler(filters.TEXT | filters.PHOTO | filters.VIDEO | filters.Document.ALL | filters.ANIMATION,
                               handle_edit_input)
            ],
            STEP_DELETE_CONFIRM: [
                CallbackQueryHandler(handle_raffle_actions)
            ]
        },

        fallbacks=[
            MessageHandler(filters.TEXT & filters.Regex("^⬅️ Назад$"), lambda u, c: ConversationHandler.END),
            MessageHandler(filters.TEXT & filters.Regex("^❌ Отмена$"), lambda u, c: ConversationHandler.END),
        ],
        name="raffles_conversation",
        persistent=False
    )
    application.add_handler(draw_channels_handler, group=2)


    draw_raffles_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.TEXT & filters.Regex("^Мои каналы 📢$"), my_channels)
        ],
        states={
            STEP_CHANNEL_1: [
                MessageHandler(filters.TEXT & filters.Regex("^🔸 Каналы Телеграмм$"), tg_channels),
                MessageHandler(filters.TEXT & filters.Regex("^⬅️Назад$"), back_channel)
            ],
        },

        fallbacks=[
            CommandHandler("start", start_command),
            CommandHandler("cancel", cancel),
        ],
        map_to_parent={
            ConversationHandler.END: MAIN_STATE
        }
    )
    application.add_handler(draw_raffles_handler, group=2)

    # Админская панель
    admin_handler = get_admin_handler()
    application.add_handler(admin_handler, group=2)

    application.add_handler(CallbackQueryHandler(add_channel_command, pattern="add_channel"), group=2)
    application.add_handler(CallbackQueryHandler(new_version, pattern="get_new_version"), group=2)
    
    # Обработчик для кнопки "Создать розыгрыш" из дашборда
    async def handle_create_raffle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает нажатие на кнопку 'Создать розыгрыш' из дашборда"""
        query = update.callback_query
        await query.answer()
        # Создаем фиктивное сообщение для запуска создания розыгрыша
        # Имитируем текстовое сообщение "Создать розыгрыш 🎁"
        from telegram import Message
        fake_message = Message(
            message_id=query.message.message_id,
            date=query.message.date,
            chat=query.message.chat,
            text="Создать розыгрыш 🎁",
            from_user=query.from_user
        )
        fake_update = Update(
            update_id=update.update_id,
            message=fake_message
        )
        await raffle_creator.start(fake_update, context)
    
    application.add_handler(CallbackQueryHandler(handle_create_raffle_callback, pattern="start_create_raffle"), group=2)

    # MessageHandler для текстовых сообщений (не команд) - последний в очереди
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message), group=3)

    logger.info("Бот запущен и готов к работе!")
    print("Бот запущен и готов к работе!")
    print("Ожидание сообщений...")
    
    # Запускаем планировщик для автоматического завершения розыгрышей в отдельном потоке
    import threading
    import asyncio
    from services.raffle_scheduler import start_scheduler
    
    def run_scheduler():
        """Запускает планировщик в отдельном event loop"""
        loop = None
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(start_scheduler())
        except Exception as e:
            print(f"❌ Критическая ошибка в планировщике: {e}")
            import traceback
            traceback.print_exc()
            # Перезапускаем планировщик через 60 секунд
            import time
            time.sleep(60)
            print("🔄 Попытка перезапуска планировщика...")
            run_scheduler()
        finally:
            if loop and not loop.is_closed():
                try:
                    loop.close()
                except:
                    pass
    
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True, name="SchedulerThread")
    scheduler_thread.start()
    logger.info("Планировщик розыгрышей запущен")
    print("✅ Планировщик розыгрышей запущен")
    
    # Запускаем polling с улучшенной обработкой ошибок
    logger.info("Запуск polling...")
    print("🔄 Запуск polling...")
    print("💡 Бот работает. Для остановки нажмите Ctrl+C")
    
    max_restart_attempts = 5
    restart_count = 0
    
    while restart_count < max_restart_attempts:
        try:
            application.run_polling(
                drop_pending_updates=True,
                close_loop=False,  # Не закрываем event loop, чтобы избежать проблем
                stop_signals=None  # Отключаем обработку сигналов для Windows
            )
            # Если polling завершился нормально (не из-за ошибки), выходим
            break
        except KeyboardInterrupt:
            logger.info("Бот остановлен пользователем")
            print("\n⏹️ Бот остановлен пользователем")
            break
        except SystemExit as e:
            logger.info(f"Бот завершен с кодом {e.code}")
            print(f"\n⏹️ Бот завершен с кодом {e.code}")
            raise
        except Exception as e:
            restart_count += 1
            logger.error(f"Ошибка при работе бота (попытка {restart_count}/{max_restart_attempts}): {e}", exc_info=True)
            print(f"\n❌ Ошибка при работе бота (попытка {restart_count}/{max_restart_attempts}): {e}")
            import traceback
            traceback.print_exc()
            
            if restart_count >= max_restart_attempts:
                print(f"\n❌ Достигнуто максимальное количество попыток перезапуска ({max_restart_attempts})")
                print("Бот завершает работу. Проверьте логи и исправьте ошибки.")
                break
            
            print(f"🔄 Перезапуск бота через 10 секунд...")
            import time
            time.sleep(10)
            
            # Пересоздаем приложение
            try:
                print("🔄 Пересоздание приложения...")
                application = ApplicationBuilder().token(bot_token).build()
                # Нужно перерегистрировать обработчики - для этого лучше перезапустить функцию bot()
                print("⚠️ Требуется полный перезапуск. Завершаем текущий процесс...")
                break
            except Exception as recreate_error:
                print(f"❌ Ошибка при пересоздании приложения: {recreate_error}")
                break

if __name__ == "__main__":
    bot()