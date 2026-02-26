"""
Админская панель для управления ботом
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler
from database.db_session import get_db
from database.models import BotUser, Raffle, Participant
from datetime import datetime


# Состояния для админской панели
ADMIN_MAIN, ADMIN_USERS, ADMIN_RAFFLES, ADMIN_STATS = range(4)


async def admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню админской панели"""
    user = update.effective_user
    
    db = next(get_db())
    bot_user = db.query(BotUser).filter_by(telegram_id=user.id).first()
    
    if not bot_user or not bot_user.is_admin:
        await update.message.reply_text(
            "❌ У вас нет прав администратора",
            parse_mode='HTML'
        )
        return ConversationHandler.END
    
    # Статистика
    total_users = db.query(BotUser).count()
    active_raffles = db.query(Raffle).filter_by(status='active').count()
    total_raffles = db.query(Raffle).count()
    premium_users = db.query(BotUser).filter(BotUser.version == 'premium').count()
    
    text = (
        f"👑 Админская панель\n\n"
        f"📊 Статистика:\n"
        f"👥 Всего пользователей: {total_users}\n"
        f"⭐ Premium пользователей: {premium_users}\n"
        f"🎁 Активных розыгрышей: {active_raffles}\n"
        f"📋 Всего розыгрышей: {total_raffles}\n"
    )
    
    keyboard = [
        [InlineKeyboardButton("👥 Управление пользователями", callback_data="admin_users")],
        [InlineKeyboardButton("🎁 Управление розыгрышами", callback_data="admin_raffles")],
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="admin_back")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        text, 
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    
    return ADMIN_MAIN


async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback для админской панели"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "admin_back" or data == "admin_back_to_main":
        from keyboards.base_keyboards import get_bot_menu
        db = next(get_db())
        bot_user = db.query(BotUser).filter_by(telegram_id=query.from_user.id).first()
        is_admin = bot_user.is_admin if bot_user else False
        db.close()
        await query.edit_message_text(
            "⚡️ Главное меню ⚡️",
            reply_markup=get_bot_menu(is_admin=is_admin),
            parse_mode='HTML'
        )
        return ConversationHandler.END
    
    elif data == "admin_users":
        return await show_users_list(update, context)
    
    elif data == "admin_raffles":
        return await show_raffles_list(update, context)
    
    elif data == "admin_stats":
        return await show_statistics(update, context)
    
    return ADMIN_MAIN


async def show_users_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список пользователей"""
    query = update.callback_query
    
    db = next(get_db())
    users = db.query(BotUser).order_by(BotUser.created_at.desc()).limit(20).all()
    
    text = "👥 Список пользователей (последние 20):\n\n"
    
    for i, user in enumerate(users, 1):
        version_emoji = "⭐" if user.version == 'premium' else "👤"
        admin_emoji = "👑" if user.is_admin else ""
        text += f"{i}. {version_emoji} {admin_emoji} @{user.username or 'без username'} (ID: {user.telegram_id})\n"
    
    keyboard = [
        [InlineKeyboardButton("⬅️ Назад", callback_data="admin_back_to_main")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text, 
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    
    return ADMIN_USERS


async def show_raffles_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список розыгрышей"""
    query = update.callback_query
    
    db = next(get_db())
    raffles = db.query(Raffle).order_by(Raffle.created_at.desc()).limit(20).all()
    
    text = "🎁 Список розыгрышей (последние 20):\n\n"
    
    for i, raffle in enumerate(raffles, 1):
        status_emoji = {
            'active': '🟢',
            'completed': '🔴',
            'pending': '🟡',
            'draft': '⚪️'
        }.get(raffle.status, '⚫️')
        
        participants_count = db.query(Participant).filter_by(raffle_id=raffle.id).count()
        
        text += f"{i}. {status_emoji} {raffle.name[:30]}... (ID: {raffle.id})\n"
        text += f"   👥 Участников: {participants_count}\n"
    
    keyboard = [
        [InlineKeyboardButton("⬅️ Назад", callback_data="admin_back_to_main")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text, 
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    
    return ADMIN_RAFFLES


async def show_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Детальная статистика"""
    query = update.callback_query
    
    db = next(get_db())
    
    # Общая статистика
    total_users = db.query(BotUser).count()
    new_users_today = db.query(BotUser).filter(
        BotUser.created_at >= datetime.now().replace(hour=0, minute=0, second=0)
    ).count()
    
    premium_users = db.query(BotUser).filter(BotUser.version == 'premium').count()
    basic_users = total_users - premium_users
    
    active_raffles = db.query(Raffle).filter_by(status='active').count()
    completed_raffles = db.query(Raffle).filter_by(status='completed').count()
    total_raffles = db.query(Raffle).count()
    
    total_participants = db.query(Participant).count()
    
    text = (
        f"📊 Детальная статистика\n\n"
        f"👥 Пользователи:\n"
        f"   Всего: {total_users}\n"
        f"   Новых сегодня: {new_users_today}\n"
        f"   Premium: {premium_users}\n"
        f"   Базовых: {basic_users}\n\n"
        f"🎁 Розыгрыши:\n"
        f"   Всего: {total_raffles}\n"
        f"   Активных: {active_raffles}\n"
        f"   Завершенных: {completed_raffles}\n\n"
        f"👤 Участия:\n"
        f"   Всего регистраций: {total_participants}\n"
    )
    
    keyboard = [
        [InlineKeyboardButton("⬅️ Назад", callback_data="admin_back_to_main")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text, 
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    
    return ADMIN_STATS


def get_admin_handler():
    """Возвращает ConversationHandler для админской панели"""
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.TEXT & filters.Regex("^👑 Админ-панель$"), admin_start)
        ],
        states={
            ADMIN_MAIN: [
                CallbackQueryHandler(admin_callback, pattern="^admin_")
            ],
            ADMIN_USERS: [
                CallbackQueryHandler(admin_callback, pattern="^admin_")
            ],
            ADMIN_RAFFLES: [
                CallbackQueryHandler(admin_callback, pattern="^admin_")
            ],
            ADMIN_STATS: [
                CallbackQueryHandler(admin_callback, pattern="^admin_")
            ]
        },
        fallbacks=[
            MessageHandler(filters.TEXT & filters.Regex("^⬅️ Назад$"), lambda u, c: ConversationHandler.END)
        ]
    )
