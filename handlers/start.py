
from telegram import Update
from telegram.ext import ContextTypes
from keyboards.base_keyboards import get_start_keyboard, get_bot_menu, get_admin_keyboard

from database.db_session import get_db
from database.models import BotUser, Channel_tg, Raffle


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    db = next(get_db())

    # ищем пользователя по telegram_id
    bot_user = db.query(BotUser).filter_by(telegram_id=user.id).first()

    # Если пользователь существует
    if bot_user:
        # channels.owner_id хранит BotUser.id (PK), поэтому используем bot_user.id
        channels_count = db.query(Channel_tg).filter_by(owner_id=bot_user.id, status='active').count()

        # Если у пользователя есть хотя бы один канал — показываем аккаунт-дашборд
        if channels_count > 0:
            user_version = bot_user.version
            active_raffles = db.query(Raffle).filter_by(owner_id=bot_user.id, status='active').count()

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

            # Показ нижнего меню
            await update.message.reply_text(
                f"💡 **Для расширения возможностей подключите расширенную версию бота!** 👇👇👇",

                reply_markup=get_admin_keyboard()
            )
            return

        # Если у пользователя есть запись, но каналов ещё нет — показываем приветствие (как и для нового)
        await update.message.reply_text(
            "👋Добро пожаловать в бот для проведения розыгрышей в\n"
            "Телеграмм каналах и группах!\n\n"
            "✅Для получения доступа к созданию розыгрышей добавьте свой\n"
            "канал в систему.\n\n"
            "✨После добавления первого канала вы\n"
            "автоматически получите доступ к функциям бота!",
            reply_markup=get_start_keyboard()
        )
        return


    # Новый пользователь: создаём запись в БД и отправляем приветствие
    new_user = BotUser(
    telegram_id=user.id,
    username=user.username,
    first_name=user.first_name,
    last_name=user.last_name,
    version='basic'
    )

    try:
        db.add(new_user)
        db.commit()
    except Exception as e:
        db.rollback()
        print("Ошибка при создании пользователя в /start:", e)
        await update.message.reply_text("Произошла внутренняя ошибка. Попробуйте снова позже.")
        return

    await update.message.reply_text(
        "👋Добро пожаловать в бот для проведения розыгрышей в\n"
        "Телеграмм каналах и группах!\n\n"
        "✅Для получения доступа к созданию розыгрышей добавьте свой\n"
        "канал в систему.\n\n"
        "✨После добавления первого канала вы\n"
        "автоматически получите доступ к функциям бота!",
        reply_markup=get_start_keyboard()
    )

