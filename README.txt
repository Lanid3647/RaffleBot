Установка базы данных PostgreSQL
brew install postgresql (установка)
brew services start postgresql (запуск)

после установки пробуем запустить
brew services start postgresql@14

проверяем как запустилось
brew services list

 У меня вылезла ошибка error и я попробовала с помощью команды посмотреть что не так:
 brew services info postgresql@14


 Далее я решила удалить базу данных и заново запустить:
 # Останавливаем
brew services stop postgresql@14

# Удаляем старую базу данных
rm -rf /usr/local/var/postgresql@14

# Создаем новую
initdb /usr/local/var/postgresql@14 --encoding=UTF8 --locale=en_US.UTF-8

# Запускаем
brew services start postgresql@14

Проверяем
brew services list

Подключаемся к PostgresSQL
psql -U $(whoami) postgres

Создаем отдельную базу данных для бота
CREATE DATABASE raffle_bot;

Создаем администратора (пользователя для базы данных)
CREATE USER bot_user WITH PASSWORD '9349386375365';

Даем пользователю все права на базу данных
GRANT ALL PRIVILEGES ON DATABASE raffle_bot TO bot_user;

Выходим из системной базы
\q

Теперь подключаемся к новой базе бота:
psql -U bot_user -d raffle_bot -W

Далее вводим пароль

Чтобы посмотреть все таблицы и создалась ли вообще база даных вводим команду
\l


Далее необходимо создать таблицы (для этого нужно написать код)
Необходимо создать базовые таблицы, которые нужны в базе данных в терминале Pycharm
python create_tables.py


(Как посмотреть версию библиотеки через терминал)
python -c "import sqlalchemy; print(sqlalchemy.__version__)"
pip show sqlalchemy
pip list | grep sqlalchemy




psql -U bot_user -d raffle_bot -W

удаляем таблиы
DROP TABLE bot_users CASCADE;
DROP TABLE channels_tg CASCADE;
DROP TABLE contest_participants CASCADE;
DROP TABLE participations CASCADE;
DROP TABLE raffles CASCADE;

Пересоздайте таблицы:
python create_tables.py

Проверьте что таблицы пересоздались:
psql -U bot_user -d raffle_bot -W

9349386375365

\dt
\d bot_users  # посмотреть структуру таблицы

SELECT * FROM table_name; посмотреть данные таблицы

-- Очистить все таблицы (быстро, сбрасывает автоинкременты)
TRUNCATE TABLE bot_users, channels_tg, contest_participants, participations, raffles CASCADE;




логирование# Настройка логирования

import  logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)









async def add_channel_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик получения ссылки на канал"""
    channel_link = update.message.text
    user = update.effective_user
    db = next(get_db())

    # Сообщаем о проверке
    await update.message.reply_text("🔄 Проверяю канал...")

    # Здесь будет реальная проверка канала через Telegram API
    # Пока имитируем успешное добавление

    # Получаем пользователя
    bot_user = db.query(BotUser).filter_by(telegram_id=user.id).first()

    new_channel_tg = Channel_tg(
        channel_id=channel_link,  # В реальности нужно извлечь ID канала
        channel_name="Название канала",  # В реальности получить через API
        channel_username=channel_link,
        owner_id=bot_user.id
    )
    db.add(new_channel_tg)
    db.commit()

    # Считаем каналы пользователя
    channels_count = db.query(Channel_tg).filter_by(owner_id=bot_user.id, is_active=True).count()

    await update.message.reply_text(
        f"✅ **Канал успешно добавлен!**\n\n"
        f"📊 **Версия:** Базовая\n\n"
        f"**Что вам доступно:**\n"
        f"📱 Telegram каналы: {channels_count}/10\n"
        f"🎁 Активные розыгрыши: 0/3\n"
        f"🏆 Максимум победителей: 10\n"
        f"✅ Автоматические розыгрыши\n"
        f"✅ Реферальная система\n"
        f"✅ Редактирование розыгрышей\n"
        f"✅ Просмотр результатов розыгрыша\n"
        f"✅ Репост в историю\n\n"
        f"**Недоступно на вашей версии:**\n"
        f"❌ Скачивание CSV\n"
        f"❌ Telegram каналы: 25\n"
        f"❌ Активные розыгрыши: 20\n"
        f"❌ Максимум победителей: не ограничено\n"
        f"❌ Проверка подписки на ВК сообщество\n"
        f"❌ Возможность самому выбирать победителя\n"
        f"❌ Статистика в реальном времени по конкурсам\n\n"
        f"💡 **Для расширения возможностей подключите расширенную версию бота!** 👇👇👇",
        reply_markup=get_bot_menu()
    )


query = update.callback_query
            await query.answer()

            await query.message.delete()


    # Отладочная информация
    logging.debug(f"Callback data: {query.data}")
    logging.debug(f"Current state: {context.user_data.get('current_step')}")


    import logging
    logging.basicConfig(level=logging.DEBUG)



draw_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.TEXT & filters.Regex("^Создать розыгрыш 🎁$"),
            type_one),
            ],
        states={


            STEP_1: [CallbackQueryHandler(type_two, pattern="^(type_auto|type_me)$"),
                     MessageHandler(filters.TEXT & ~filters.COMMAND, type_one)
                     ],

            STEP_2: [MessageHandler(filters.TEXT & ~filters.COMMAND, type_three),
                     ],

            STEP_3: [MessageHandler(filters.TEXT & ~filters.COMMAND, type_four),
                     ],
            STEP_4: [CallbackQueryHandler(type_five, pattern="^(time_start|time_end)$"),
                     MessageHandler(filters.TEXT & ~filters.COMMAND, handler_start_time_input)],

            STEP_5: [MessageHandler(filters.TEXT & ~filters.COMMAND, type_six),

                     ],
            STEP_6: [MessageHandler(filters.ALL, type_seven)],
            STEP_7: [CallbackQueryHandler(type_eight, pattern="referral_")],
            STEP_8: [CallbackQueryHandler(handle_step_eight_actions, pattern="^select_channel_"),
                CallbackQueryHandler(handle_step_eight_actions, pattern="^continue_to_next_step$"),
                CallbackQueryHandler(handle_step_eight_actions, pattern="^back_to_previous_step$"),],

            STEP_9: [CallbackQueryHandler(handle_step_eight_actions_nine, pattern="^select_channel_"),
                CallbackQueryHandler(handle_step_eight_actions_nine, pattern="^continue_to_next_step$"),
                CallbackQueryHandler(handle_step_eight_actions_nine, pattern="^back_to_previous_step$"),
            ],

            STEP_10: [
                CallbackQueryHandler(
                    handle_step_ten_actions,
                    pattern="^(luck_boost|captcha|save_raffle|back_to_previous_step|cancel_creation)$"
                )
            ],




# Функция обработки "Назад" на шаге 4
"""async def back_from_step_4(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # Сбрасываем флаг ожидания времени
    context.user_data.pop('waiting_for_start_time', None)

    # Устанавливаем текущий шаг на 3
    context.user_data['current_step'] = STEP_3

    # Удаляем сообщения шага 4, если они есть
    step4_message_id = context.user_data.get('step4_message_id')
    step4_chat_id = context.user_data.get('step4_chat_id')
    if step4_message_id and step4_chat_id:
        try:
            await context.bot.delete_message(chat_id=step4_chat_id, message_id=step4_message_id)
        except:
            pass

    stepa4_message_id = context.user_data.get('stepa4_message_id')
    stepa4_chat_id = context.user_data.get('stepa4_chat_id')
    if stepa4_message_id and stepa4_chat_id:
        try:
            await context.bot.delete_message(chat_id=stepa4_chat_id, message_id=stepa4_message_id)
        except:
            pass

    # Переходим напрямую к шагу 3
    if update.callback_query:
        # Ответим на callback
        await update.callback_query.answer()
        upd = update.callback_query
    else:
        upd = update

    # Вызываем type_three напрямую, без back_to_previous
    return await type_three(upd, context)"""

async def back_from_step_4(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # Сбрасываем флаг ожидания времени
    context.user_data.pop('waiting_for_start_time', None)

    # Устанавливаем текущий шаг
    context.user_data['current_step'] = STEP_3

    # Удаляем сообщения шага 4
    for key in ['step4_message_id', 'stepa4_message_id']:
        msg_id = context.user_data.get(key)
        chat_id = context.user_data.get(f"{key.split('_')[0]}_chat_id")
        if msg_id and chat_id:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
            except:
                pass

    # Показываем сообщение пользователю для шага 3
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(
            f"📝 Шаг 3 из 11: Служебное название\n\n"

            f"Введите служебное название розыгрыша для обозначения в боте:\n",
            reply_markup = get_bot_menu_draw_1()
        )
    else:
        await update.message.reply_text(
            f"📝 Шаг 3 из 11: Служебное название\n\n"

            f"Введите служебное название розыгрыша для обозначения в боте:\n",
            reply_markup = get_bot_menu_draw_1()
        )

    # Возвращаем STEP_3 для ConversationHandler
    return STEP_3


 # УНИВЕРСАЛЬНАЯ ФУНКЦИЯ - работает с callback_query и message
    if update.callback_query and update.callback_query.data == "back_to_previous_step":
        return await back_to_previous(update, context)
    if update.message and update.message.text.strip() == "⬅️Назад":
        return await back_to_previous(update, context)
    if update.message and update.message.text.strip() == "❌Отменить создание":
        return await close_type(update, context)




async def back_to_previous(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    # Получаем текущее состояние
    current_state = context.user_data.get('current_step', STEP_1)

    # СБРАСЫВАЕМ ДАННЫЕ ВВОДА ПРИ ВОЗВРАТЕ НАЗАД
    context.user_data.pop('waiting_for_input', None)
    # Логика возврата на предыдущий шаг
    if update.callback_query:
        upd = update.callback_query
    else:
        upd = update

    if current_state == STEP_2:
        # Возвращаемся к шагу 1
        return await type_one(upd, context)

    elif current_state == STEP_3:
        return await type_two(update, context)

    elif current_state == STEP_4:
        return await type_three(update, context)

    elif current_state == STEP_3:
        return await type_four(update, context)



    elif current_state == STEP_6:
        return await type_five(update, context)

    elif current_state == STEP_7:
        return await type_six(update, context)

    elif current_state == STEP_8:
        return await type_seven(update, context)

    elif current_state == STEP_9:
        return await type_eight(update, context)




""" if update.callback_query:
        data = update.callback_query.data
        if data == "back_to_previous":
            return await back_from_step_4(update, context)
        if data == "cancel_creation":
            return await close_type(update, context)
    elif update.message:
        text = update.message.text.strip()
        if text == "⬅️Назад":
            return await back_from_step_4(update, context)
        if text == "❌Отменить создание":
            return await close_type(update, context)"""
