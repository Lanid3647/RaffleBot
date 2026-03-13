from keyboards.base_keyboards import get_channels, get_bot_menu, add_channels
from telegram import Update, Message, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from database.db_session import get_db
from database.models import Channel_tg, BotUser

STEP_CHANNEL_1, STEP_CHANNEL_2, STEP_CHANNEL_3 = range(3)
MAIN_STATE = 0

async def my_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    reply_markup = get_channels()

    await message.reply_text(
        "🔥 Выберите нужный список каналов:",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    return STEP_CHANNEL_1

async def tg_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user=update.effective_user


    if update.message:
        message = update.message
        db = next(get_db())
        bot_user = db.query(BotUser).filter_by(telegram_id=user.id).first()

        user_channels = db.query(Channel_tg).filter_by(owner_id=bot_user.id, status='active').all()
        channels_count = len(user_channels)

        # Формируем текст сообщения
        text = (
            f"🗒 Мои каналы\n\n"
            f"🎯 Активных: {channels_count}/10\n\n"

        )
        # Добавляем список каналов в текст
        if user_channels:
            text += "📢 Ваши каналы:\n"
            for i, channel in enumerate(user_channels, 1):
                channel_name = channel.channel_name or channel.channel_username or f"Канал {i}"
                text += f"{i}. {channel_name}\n"

        else:
            text += "📭 У вас пока нет добавленных каналов\n"

        # Создаем inline кнопки
        keyboard = []

        # Кнопки для каждого канала
        for channel in user_channels:
            channel_name = channel.channel_name or channel.channel_username or f"Канал {channel.id}"
            keyboard.append([
                InlineKeyboardButton(
                    f"⚙️ {channel_name}",
                    callback_data=f"manage_channel_{channel.id}"
                )
            ])

        reply_markup=add_channels()

        await message.reply_text(
            text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

        return STEP_CHANNEL_1

async def back_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    reply_markup = get_bot_menu()
    await message.reply_text(
        "⭐️ Главное меню ⭐️",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

    return ConversationHandler.END
