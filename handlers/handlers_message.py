import time
import re # стандартный модуль для регулярных выражений
import asyncio # задержка перед отправкой сообщения
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError
from database.db_session import get_db
from database.models import BotUser, Channel_tg, Raffle
from keyboards.base_keyboards import get_bot_menu, get_admin_keyboard, get_keyboard_draw_1, get_bot_menu_draw_1
from handlers.channel_handlers_keyboards import my_channels


# Простая регулировка для форматов: https://t.me/name, @name, -100123...
CHANNEL_LINK_RE = re.compile(r'^(https?://t\.me/)?@?([A-Za-z0-9_]{5,})$|^(-100\d+)$')


#Проверка прав бота в чате
async def check_bot_permissions_in_chat(context, chat_identifier):
        # Возвращает (ok: bool, reason: str, chat_obj_or_None)

        try:
            chat = await context.bot.get_chat(chat_identifier)
        except TelegramError as e:
            return False, ("Не удалось получить информацию о канале. "
                       "Если канал приватный — добавьте бота в администраторы и пришлите ссылку снова."), None
        except Exception as e:
            return False, f"Ошибка при получении чата: {e}", None

        try:
            me = await context.bot.get_me()
            bot_id = me.id
        except Exception as e:
            return False,  f"Не удалось получить данные бота: {e}", chat


        try:
            member = await context.bot.get_chat_member(chat.id, bot_id)
        except TelegramError:
            # бот не в чате (чаще приватный канал) или API не возвращает
            return False, "Бот не состоит в этом канале/группе. Добавьте бота в администраторы и повторите.", chat
        except Exception as e:
            return False,  f"Ошибка при проверке статуса бота: {e}", chat


        status = member.status # 'creator', 'administrator', 'member', 'left', 'kicked'
        if status in ("creator", "administrator"):
         # Проверяем ключевые права (для каналов важно, чтобы бот мог публиковать)
        # member может иметь атрибуты can_post_messages (для channels) или can_send_messages (для супергрупп)

            can_post = getattr(member, "can_post_messages", None)
            can_send = getattr(member, "can_send_messages", None)

            # Если явно False — нет права

            if can_post is False:
                return False, "У бота нет права публиковать сообщения (can_post_messages=False). Включите его.", chat
            if can_send is False:
                return False, "У бота нет права отправлять сообщения в этом чате. Включите его.", chat

            # В остальных случаях считаем OK
            return True, "Бот — администратор и имеет необходимые права.", chat

        if status == "member":
            return False, "Бот присутствует в чате, но не является администратором. Дайте права администратора.", chat
        if status in ("left", "kicked"):
            return False, "Бот не добавлен в канал/был удалён. Добавьте бота в администраторы.", chat

        return False, f"Неожиданный статус бота: {status}", chat






async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):


    if not update.message or not update.message.text:
        return


    text = update.message.text.strip()
    user = update.effective_user
    user_id = user.id

    if text == "✨ Расширенная версия бота✨\n❗️Включая ВК ❗️":
        await update.message.reply_text(
            f"📈 Подключение расширенной версии\n\n"

            f"🔵 Цена - 1990₽/мес\n"
            f"✅ Telegram каналы: 25\n"
            f"✅ Активные розыгрыши: 20\n"
            f"✅ Максимум победителей: не ограничено\n"
            f"✅ Автоматические розыгрыши\n"
            f"✅ Реферальная система\n"
            f"✅ Редактирование розыгрышей\n"
            f"✅Просмотр результатов розыгрыша\n"
            f"✅Репост в историю\n"
            f"✅Скачивание CSV\n"
            f"✅Проверка подписки на ВК сообщество\n"
            f"✅Возможность самому выбирать победителя\n"
            f"✅Статистика в реальном времени по конкурсам\n\n"


            f"📞 Для подключения расширенной версии обратитесь:\n"
            f"👤 @XXXX\n"
        )

    #elif text == "Мои каналы 📢":
   #     return await my_channels(update, context)



    elif text == "Техническая поддержка ⁉️":
        await update.message.reply_text(
            f"Техническая поддержка ⁉️\n"
            f"Возникли вопросы? \n\n"
            f"Напишите здесь, и мы обязательно поможем!\n"
            f"👤 @XXXX\n"
        )

    elif text == "О боте ℹ️":
        await update.message.reply_text(
            f"ℹ️ О боте\n\n\n"
            f"🎯 Наша миссия\n\n"
            f"Создать лучший инструмент для проведения честных и прозрачных розыгрышей в социальных сетях.\n\n"
            f"🏆 Преимущества:\n\n"
            f"• CSV таблица участников с множеством данных, которые помогут вам выявить ботов и нечестных участников. Если рандом выдал победу жулику, вы сможете поступить с призом на свое усмотрение.\n\n"
            f"• Возможность проводить самостоятельные розыгрыши без автоматического выбора победителей.\n\n"
            f"• Подключение к розыгрышам ваших VK каналов.\n\n"
            f"• Возможность репоста розыгрыша в историю\n\n"
            f"• Реферальная система\n\n"
            f"• Возможность  редактирования розыгрышей\n\n"
            f"• Возможность самому выбирать победителя\n\n"
            f"• Статистика в реальном времени по конкурсам\n\n"
        )


    # Таймаут режима добавления канала
    # Авто-истечение флага (например, 10 минут)
    if context.user_data.get('adding_channel'):
        ts = context.user_data.get('adding_channel_ts', 0)
        if int(time.time()) - ts > 60 * 10:
            context.user_data.pop('adding_channel', None)
            context.user_data.pop('adding_channel_ts', None)

    # Проверка - мы в режиме добавления или нет, Если в режиме добавления — обрабатываем как ссылку

    if context.user_data.get('adding_channel'):
        # Проверяем формат(соответствует ли ссылка формату)
        match = CHANNEL_LINK_RE.match(text)
        if not match:
            await update.message.reply_text(
                "Неверный формат. Пришлите @channel_name, https://t.me/channel_name или ID (-100...)"
            )
            return

        # Нормализуем вход (парсинг username / id)
        # Преобразует то, что прислал пользователь, в два понятных значения:
        channel_username = None
        channel_id_input = None

        if text.startswith('https://t.me/'):
            channel_username = text.split('https://t.me/')[-1].strip('/')
            chat_identifier = f"@{channel_username}"

        elif text.startswith('@'):
            channel_username = text[1:].strip()
            chat_identifier = f"@{channel_username}"

        else:
            # возможно ID -100...
            channel_id_input = text.strip()
            chat_identifier = channel_id_input


        # 1) Проверяем права бота в чате
        ok, reason, chat = await check_bot_permissions_in_chat(context, chat_identifier)
        if not ok:
            await update.message.reply_text(
                f"❌Проверка прав не пройдена: {reason}\n\n\n"
                "⚙️Инструкция:\n\n"
                
                "1) Добавьте бота в администраторы канала.\n"
                "2) Дайте права: отправка сообщений и редактирование сообщений.\n"
                "3) Если канал приватный — после добавления пришлите ссылку снова."
            )
            return

        # Подготовим значение для обязательного поля channel_id в БД.
        # Если реального числового ID нет — подставим @username в поле channel_id,
        # а username запишем в отдельное поле channel_username.
        # 2) Если ok — берем реальный chat.id (желательно), иначе используем подставленный @username
        db_channel_id_value = str(chat.id) if chat and getattr(chat, "id", None) else (f"@{channel_username}" if channel_username else channel_id_input)

        db = next(get_db())
        bot_user = db.query(BotUser).filter_by(telegram_id=user_id).first()
        # Находим пользователя (BotUser) по telegram_id

        if not bot_user:
            await update.message.reply_text("Не могу найти ваш профиль в базе — напишите /start.")
            context.user_data.pop('adding_channel', None)
            context.user_data.pop('adding_channel_ts', None)
            return

        # Проверка дубликата — ищем по channel_id (реальному или @username) или по channel_username
        exists = db.query(Channel_tg).filter_by(channel_id=db_channel_id_value, owner_id=bot_user.id).first()
        if not exists and channel_username:
            exists = db.query(Channel_tg).filter_by(channel_username=channel_username, owner_id=bot_user.id).first()


        if exists:
            # очищаем режим
            await update.message.reply_text("Этот канал уже добавлен в систему.")
            context.user_data.pop('adding_channel', None)
            context.user_data.pop('adding_channel_ts', None)
            return


        new_ch = Channel_tg(
            channel_id=db_channel_id_value,
            channel_name=chat.title if chat and getattr(chat, "title", None) else None,
            channel_username=channel_username if channel_username else None,
            owner_id=bot_user.id,
            status='active',
            is_active=True
        )

        db.add(new_ch)
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            # Логируем ошибку в консоль для отладки
            print("DB commit error:", e)
            await update.message.reply_text("Ошибка при сохранении канала. Попробуйте снова позже.")
            # очищаем режим (опционально можно оставить)
            context.user_data.pop('adding_channel', None)
            context.user_data.pop('adding_channel_ts', None)
            return

        # ищем пользователя по telegram_id
        bot_user = db.query(BotUser).filter_by(telegram_id=user.id).first()
        user_version = bot_user.version
        active_raffles = db.query(Raffle).filter_by(owner_id=bot_user.id, status='active').count()
        channels_count = db.query(Channel_tg).filter_by(owner_id=bot_user.id, status='active').count()


        await update.message.reply_text ("🔄 Проверка канала...")
        await asyncio.sleep(1.5)

        await update.message.reply_text("Канал успешно добавлен ✅")
        await asyncio.sleep(1)


        await update.message.reply_text(
                 f"👤 Админ: {user.id} ({f'@{user.username}' if user.username else user.first_name})\n"
                f"📊 Версия: {user_version}\n\n"
                f" Что вам доступно: \n"
                f"📱 Telegram каналы: {channels_count}/10\n"
                f"🎁 Активные розыгрыши: {active_raffles}/3\n"
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
                f"❌ Статистика в реальном времени по конкурсам\n\n",

                reply_markup=get_bot_menu()
        )

        await update.message.reply_text(
            f"💡 **Для расширения возможностей подключите расширенную версию бота!** 👇👇👇",

            reply_markup=get_admin_keyboard()
        )
        # очищаем режим
        context.user_data.pop('adding_channel', None)
        context.user_data.pop('adding_channel_ts', None)
        return

    # --- обычная обработка, если не в режиме добавления ---
    #await update.message.reply_text(
        "Я получил сообщение, но не жду ссылку на канал. Нажмите «Добавить канал» в меню."


    # Если не в режиме добавления — можно игнорировать или обрабатывать сообщения из меню
    return



# /cancel команда для отмены режима добавления
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.pop('adding_channel', None):
        context.user_data.pop('adding_channel_ts', None)
        await update.message.reply_text("Операция добавления канала отменена.")
    else:
        await update.message.reply_text("Нет активных операций для отмены.")












