from database.models import Participant, BotUser, Raffle
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
from database.db_session import get_db


# Состояния для ConversationHandler
STEP_RAFFLES_1, STEP_RAFFLES_2, STEP_RAFFLES_3, STEP_EDIT_1, STEP_EDIT_2, STEP_DELETE_CONFIRM = range(6)


async def my_raffles_start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    db = next(get_db())
    bot_user = db.query(BotUser).filter_by(telegram_id=user.id).first()

    if not bot_user:
        await update.message.reply_text(
            "❌ Пользователь не найден",
            parse_mode='HTML'
        )
        return ConversationHandler.END

    # Получаем все розыгрыши пользователя
    user_raffles = db.query(Raffle).filter_by(owner_id=user.id).order_by(Raffle.created_at.desc()).all()

    # Подсчитываем активные розыгрыши
    active_raffles = [r for r in user_raffles if r.status == 'active']
    active_count = len(active_raffles)

    # Формируем текст сообщения
    if user_raffles:
        text = (
            f"🗒 Мои розыгрыши\n\n"
            f"🎯 Активных: {active_count}/3\n"
            f"📊 Всего: {len(user_raffles)}/25\n\n"
        )
    else:
        text = (
            f"🗒 Мои розыгрыши\n\n"
            f"🎯 Активных: 0/3\n"
            f"📊 Всего: 0/25\n\n"
            f"📭 У вас пока нет добавленных розыгрышей\n"
        )

    # Создаем inline кнопки для розыгрышей
    keyboard = []

    for raffle in user_raffles:
        # Форматируем даты
        start_date = raffle.start_date.strftime("%d.%m.%Y") if raffle.start_date else "Нет даты"
        end_date = raffle.end_date.strftime("%d.%m.%Y") if raffle.end_date else "Нет даты"

        # Определяем статус и смайлик
        if raffle.status == 'active':
            emoji = "🟢"  # Зеленый смайлик для активных
        elif raffle.status == 'completed':
            emoji = "🔴"  # Красный смайлик для завершенных
        elif raffle.status == 'pending':
            emoji = "🟡"  # Желтый для ожидающих
        elif raffle.status == 'draft':
            emoji = "⚪️"  # Белый для черновиков
        else:
            emoji = "⚫️"

        # Обрезаем длинное название
        raffle_name = raffle.name[:20] + "..." if len(raffle.name) > 20 else raffle.name

        # Создаем текст кнопки
        button_text = f"{emoji} {raffle_name} ({start_date}-{end_date})"

        # Создаем callback_data с ID розыгрыша
        callback_data = f"raffle_{raffle.id}"

        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])

    # Добавляем кнопку "Назад" если есть розыгрыши
    if user_raffles:
        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")])
    else:
        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправляем сообщение
    await update.message.reply_text(
        text, 
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

    return STEP_RAFFLES_1


async def handle_raffle_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "back_to_main":
        # Возвращаемся в главное меню
        from keyboards.base_keyboards import get_bot_menu
        await query.edit_message_text(
            "⚡️ Главное меню ⚡️",
            reply_markup=get_bot_menu(),
            parse_mode='HTML'
        )
        return ConversationHandler.END

    elif data.startswith("raffle_"):
        raffle_id = int(data.split("_")[1])

        db = next(get_db())
        raffle = db.query(Raffle).filter_by(id=raffle_id).first()

        if raffle:
            # Сохраняем ID розыгрыша в context для использования в других шагах
            context.user_data['current_raffle_id'] = raffle_id

            # Формируем детальную информацию о розыгрыше
            start_date = raffle.start_date.strftime("%d.%m.%Y %H:%M") if raffle.start_date else "Не указано"
            end_date = raffle.end_date.strftime("%d.%m.%Y %H:%M") if raffle.end_date else "Не указано"
            created_at = raffle.created_at.strftime("%d.%m.%Y %H:%M") if raffle.created_at else "Не указано"

            # Получаем статистику участия
            participants_count = db.query(Participant).filter_by(raffle_id=raffle_id).count()

            # Определяем статус
            if raffle.status == 'active':
                status_text = "🟢 Активен"
            elif raffle.status == 'completed':
                status_text = "🔴 Завершен"
            elif raffle.status == 'pending':
                status_text = "🟡 Ожидает начала"
            elif raffle.status == 'draft':
                status_text = "⚪️ Черновик"
            else:
                status_text = raffle.status

            text = (
                f"📋 Детали розыгрыша\n\n"
                f"🏷 Название: {raffle.name}\n"
                f"📊 Статус: {status_text}\n"
                f"👥 Участников: {participants_count}\n"
                f"🏆 Победителей: {raffle.winners_count}\n"
                f"⏰ Начало: {start_date}\n"
                f"⏰ Окончание: {end_date}\n"
                f"📅 Создан: {created_at}\n"
                f"🤖 Тип: {'Автоматический' if raffle.winner_type == 'auto' else 'Самостоятельный'}\n"
            )

            # Кнопки управления розыгрышем в зависимости от статуса
            keyboard = []

            if raffle.status == 'active':
                # Для активных розыгрышей
                keyboard.append([InlineKeyboardButton("📥 Посмотреть результаты", callback_data=f"results_{raffle.id}")])
                keyboard.append([InlineKeyboardButton("✏️ Редактировать розыгрыш", callback_data=f"edit_{raffle.id}")])
                keyboard.append([InlineKeyboardButton("⏹ Остановить розыгрыш", callback_data=f"stop_{raffle.id}")])
                keyboard.append([InlineKeyboardButton("🗑 Удалить розыгрыш", callback_data=f"delete_{raffle.id}")])
            elif raffle.status == 'completed':
                # Для завершенных розыгрышей
                keyboard.append([InlineKeyboardButton("📥 Посмотреть результаты", callback_data=f"results_{raffle.id}")])
                keyboard.append([InlineKeyboardButton("🗑 Удалить розыгрыш", callback_data=f"delete_{raffle.id}")])
            elif raffle.status == 'pending':
                # Для ожидающих розыгрышей
                keyboard.append([InlineKeyboardButton("✏️ Редактировать розыгрыш", callback_data=f"edit_{raffle.id}")])
                keyboard.append([InlineKeyboardButton("🗑 Удалить розыгрыш", callback_data=f"delete_{raffle.id}")])
            elif raffle.status == 'draft':
                # Для черновиков
                keyboard.append([InlineKeyboardButton("✏️ Редактировать розыгрыш", callback_data=f"edit_{raffle.id}")])
                keyboard.append([InlineKeyboardButton("🗑 Удалить розыгрыш", callback_data=f"delete_{raffle.id}")])

            # Кнопка "Назад к списку" всегда
            keyboard.append([InlineKeyboardButton("⬅️ Назад к списку", callback_data="back_to_list")])

            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                text, 
                reply_markup=reply_markup,
                parse_mode='HTML'
            )

            return STEP_RAFFLES_2

    return STEP_RAFFLES_1


async def handle_raffle_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "back_to_list":
        # Возвращаемся к списку розыгрышей
        return await my_raffles_start(update, context)

    elif data.startswith("results_"):
        raffle_id = int(data.split("_")[1])
        return await show_results(update, context, raffle_id)

    elif data.startswith("edit_"):
        raffle_id = int(data.split("_")[1])
        return await start_editing(update, context, raffle_id)

    elif data.startswith("stop_"):
        raffle_id = int(data.split("_")[1])
        return await stop_raffle(update, context, raffle_id)

    elif data.startswith("delete_"):
        raffle_id = int(data.split("_")[1])
        return await confirm_delete(update, context, raffle_id)
    
    elif data.startswith("csv_"):
        raffle_id = int(data.split("_")[1])
        return await download_csv(update, context, raffle_id)

    elif data == "cancel_edit":
        # Отмена редактирования - возвращаемся к деталям розыгрыша
        raffle_id = context.user_data.get('current_raffle_id')
        if raffle_id:
            return await show_raffle_details(update, context, raffle_id)
        else:
            return await my_raffles_start(update, context)

    elif data == "confirm_delete":
        raffle_id = context.user_data.get('raffle_to_delete')
        if raffle_id:
            return await delete_raffle(update, context, raffle_id)
        else:
            return await my_raffles_start(update, context)

    elif data == "cancel_delete":
        raffle_id = context.user_data.get('raffle_to_delete')
        if raffle_id:
            return await show_raffle_details(update, context, raffle_id)
        else:
            return await my_raffles_start(update, context)

    return STEP_RAFFLES_2


async def show_results(update: Update, context: ContextTypes.DEFAULT_TYPE, raffle_id: int):

    query = update.callback_query
    db = next(get_db())

    raffle = db.query(Raffle).filter_by(id=raffle_id).first()

    if not raffle:
        await query.answer("❌ Розыгрыш не найден", show_alert=True)
        return await my_raffles_start(update, context)

    # Получаем статистику
    participants_count = db.query(Participant).filter_by(raffle_id=raffle_id).count()
    winners_count = db.query(Participant).filter_by(raffle_id=raffle_id, is_winner=True).count()

    # Получаем список участников
    participants = db.query(Participant).filter_by(raffle_id=raffle_id).all()

    text = (
        f"📊 Результаты розыгрыша\n\n"
        f"🏷 Название: {raffle.name}\n"
        f"👥 Всего участников: {participants_count}\n"
        f"🏆 Победителей: {winners_count}/{raffle.winners_count}\n"
    )

    if raffle.status == 'completed' and winners_count > 0:
        text += f"\n🏆 Победители:\n"
        winners = db.query(Participant).filter_by(raffle_id=raffle_id, is_winner=True).all()
        for i, winner in enumerate(winners, 1):
            username = winner.username or f"ID: {winner.user_id}"
            text += f"{i}. @{username}\n"
    elif participants_count > 0:
        text += f"\n📋 Список участников (первые 20):\n"
        for i, participant in enumerate(participants[:20], 1):
            username = participant.username or f"ID: {participant.user_id}"
            text += f"{i}. @{username}\n"

    if participants_count > 20:
        text += f"\n... и еще {participants_count - 20} участников"

    # Кнопки для возврата и CSV
    keyboard = []
    if participants_count > 0:
        keyboard.append([InlineKeyboardButton("📥 Скачать CSV", callback_data=f"csv_{raffle_id}")])
    keyboard.append([InlineKeyboardButton("⬅️ Назад к розыгрышу", callback_data=f"raffle_{raffle_id}")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text, 
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

    return STEP_RAFFLES_2


async def start_editing(update: Update, context: ContextTypes.DEFAULT_TYPE, raffle_id: int):

    query = update.callback_query

    # Сохраняем ID розыгрыша для редактирования
    context.user_data['editing_raffle_id'] = raffle_id

    text = (
        f"✏️ Редактирование розыгрыша\n\n"
        f"Что вы хотите изменить?\n\n"
        f"Вы можете изменить:\n"
        f"1. Текст описания\n"
        f"2. Медиафайл (картинку/видео)\n"
        f"3. Название розыгрыша\n"
    )

    keyboard = [
        [InlineKeyboardButton("📝 Изменить текст", callback_data=f"edit_text_{raffle_id}")],
        [InlineKeyboardButton("🖼 Изменить медиа", callback_data=f"edit_media_{raffle_id}")],
        [InlineKeyboardButton("🏷 Изменить название", callback_data=f"edit_name_{raffle_id}")],
        [InlineKeyboardButton("❌ Отменить редактирование", callback_data="cancel_edit")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text, 
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

    return STEP_EDIT_1


async def handle_edit_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith("edit_text_"):
        raffle_id = int(data.split("_")[2])
        context.user_data['edit_mode'] = 'text'
        await query.edit_message_text(
            "📝 Введите новый текст для розыгрыша:\n\n"
            "Вы можете использовать HTML разметку:\n"
            "• <b>жирный</b>\n"
            "• <i>курсив</i>\n"
            "• <u>подчеркнутый</u>\n"
            "• <a href='ссылка'>текст</a>\n\n"
            "Отправьте текст или напишите 'отмена' для отмены:",
            parse_mode='HTML'
        )
        return STEP_EDIT_2

    elif data.startswith("edit_media_"):
        raffle_id = int(data.split("_")[2])
        context.user_data['edit_mode'] = 'media'
        await query.edit_message_text(
            "🖼 Отправьте новое фото или видео для розыгрыша:\n\n"
            "Вы можете отправить:\n"
            "• Фото\n"
            "• Видео\n"
            "• GIF\n"
            "• Документ\n\n"
            "Или напишите 'удалить' чтобы удалить медиафайл\n"
            "Или 'отмена' для отмены:",
            parse_mode='HTML'
        )
        return STEP_EDIT_2

    elif data.startswith("edit_name_"):
        raffle_id = int(data.split("_")[2])
        context.user_data['edit_mode'] = 'name'
        await query.edit_message_text(
            "🏷 Введите новое название для розыгрыша:\n\n"
            "Или напишите 'отмена' для отмены:",
            parse_mode='HTML'
        )
        return STEP_EDIT_2

    return STEP_EDIT_1


async def handle_edit_input(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message:
        message = update.message
        text = message.text.strip().lower() if message.text else ""

        raffle_id = context.user_data.get('editing_raffle_id')
        edit_mode = context.user_data.get('edit_mode')

        db = next(get_db())
        raffle = db.query(Raffle).filter_by(id=raffle_id).first()

        if not raffle:
            await message.reply_text(
                "❌ Розыгрыш не найден",
                parse_mode='HTML'
            )
            return await my_raffles_start(update, context)

        if text == 'отмена':
            # Возвращаемся к выбору что редактировать
            return await start_editing(update, context, raffle_id)

        if edit_mode == 'text':
            if text == 'удалить':
                raffle.media_caption = ""
                db.commit()
                await message.reply_text(
                    "✅ Текст удален",
                    parse_mode='HTML'
                )
            else:
                raffle.media_caption = message.text
                db.commit()
                await message.reply_text(
                    "✅ Текст обновлен",
                    parse_mode='HTML'
                )

        elif edit_mode == 'name':
            raffle.name = message.text
            db.commit()
            await message.reply_text(
                "✅ Название обновлено",
                parse_mode='HTML'
            )

        elif edit_mode == 'media':
            if text == 'удалить':
                raffle.media_type = None
                raffle.media_file_id = None
                db.commit()
                await message.reply_text(
                    "✅ Медиафайл удален",
                    parse_mode='HTML'
                )
            elif message.photo:
                raffle.media_type = 'photo'
                raffle.media_file_id = message.photo[-1].file_id
                db.commit()
                await message.reply_text(
                    "✅ Фото обновлено",
                    parse_mode='HTML'
                )
            elif message.video:
                raffle.media_type = 'video'
                raffle.media_file_id = message.video.file_id
                db.commit()
                await message.reply_text(
                    "✅ Видео обновлено",
                    parse_mode='HTML'
                )
            elif message.animation:
                raffle.media_type = 'animation'
                raffle.media_file_id = message.animation.file_id
                db.commit()
                await message.reply_text(
                    "✅ GIF обновлен",
                    parse_mode='HTML'
                )
            elif message.document:
                raffle.media_type = 'document'
                raffle.media_file_id = message.document.file_id
                db.commit()
                await message.reply_text(
                    "✅ Документ обновлен",
                    parse_mode='HTML'
                )
            else:
                await message.reply_text(
                    "❌ Пожалуйста, отправьте фото, видео или напишите 'удалить'/'отмена'",
                    parse_mode='HTML'
                )
                return STEP_EDIT_2

        # Возвращаемся к деталям розыгрыша
        return await show_raffle_details(update, context, raffle_id)

    return STEP_EDIT_2


async def stop_raffle(update: Update, context: ContextTypes.DEFAULT_TYPE, raffle_id: int):

    query = update.callback_query

    db = next(get_db())
    raffle = db.query(Raffle).filter_by(id=raffle_id).first()

    if not raffle:
        await query.answer("❌ Розыгрыш не найден", show_alert=True)
        return await my_raffles_start(update, context)

    if raffle.status != 'active':
        await query.answer("❌ Можно остановить только активные розыгрыши", show_alert=True)
        return await show_raffle_details(update, context, raffle_id)

    raffle.status = 'completed'
    db.commit()

    await query.answer("✅ Розыгрыш остановлен", show_alert=True)

    # Возвращаемся к деталям розыгрыша
    return await show_raffle_details(update, context, raffle_id)


async def confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE, raffle_id: int):

    query = update.callback_query

    # Сохраняем ID розыгрыша для удаления
    context.user_data['raffle_to_delete'] = raffle_id

    db = next(get_db())
    raffle = db.query(Raffle).filter_by(id=raffle_id).first()

    text = (
        f"⚠️ Подтверждение удаления\n\n"
        f"Вы действительно хотите удалить розыгрыш?\n\n"
        f"🏷 Название: {raffle.name}\n"
        f"📊 Статус: {raffle.status}\n"
        f"📅 Создан: {raffle.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"❌ Это действие нельзя отменить!\n"
        f"Все данные об участии будут удалены."
    )

    keyboard = [
        [InlineKeyboardButton("✅ Да, удалить", callback_data="confirm_delete")],
        [InlineKeyboardButton("❌ Нет, отменить", callback_data="cancel_delete")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text, 
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

    return STEP_DELETE_CONFIRM


async def delete_raffle(update: Update, context: ContextTypes.DEFAULT_TYPE, raffle_id: int):

    query = update.callback_query

    db = next(get_db())
    raffle = db.query(Raffle).filter_by(id=raffle_id).first()

    if not raffle:
        await query.answer("❌ Розыгрыш не найден", show_alert=True)
        return await my_raffles_start(update, context)

    # Удаляем связанные участия
    db.query(Participant).filter_by(raffle_id=raffle_id).delete()

    # Удаляем розыгрыш
    db.delete(raffle)
    db.commit()

    await query.answer("✅ Розыгрыш удален", show_alert=True)

    # Очищаем данные
    if 'raffle_to_delete' in context.user_data:
        del context.user_data['raffle_to_delete']

    # Возвращаемся к списку розыгрышей
    return await my_raffles_start(update, context)


async def show_raffle_details(update: Update, context: ContextTypes.DEFAULT_TYPE, raffle_id: int):

    # Если это callback query, редактируем сообщение
    if update.callback_query:
        query = update.callback_query
        # Создаем fake update для использования существующей логики
        return await handle_raffle_selection(update, context)
    else:
        # Если это обычное сообщение, создаем новый контекст
        from telegram import Update
        from telegram.ext import CallbackContext

        # Нужно адаптировать логику для работы с обычным сообщением
        # В данном случае просто возвращаем к началу
        return await my_raffles_start(update, context)


async def download_csv(update: Update, context: ContextTypes.DEFAULT_TYPE, raffle_id: int):
    """Генерирует и отправляет CSV файл с участниками"""
    from services.csv_export import generate_csv_for_raffle, get_csv_filename
    from telegram import InputFile
    import io
    
    query = update.callback_query
    await query.answer()
    
    db = next(get_db())
    raffle = db.query(Raffle).filter_by(id=raffle_id).first()
    
    if not raffle:
        await query.answer("❌ Розыгрыш не найден", show_alert=True)
        return STEP_RAFFLES_2
    
    # Генерируем CSV
    csv_content = generate_csv_for_raffle(raffle_id)
    
    if not csv_content:
        await query.answer("❌ Ошибка при генерации CSV", show_alert=True)
        return STEP_RAFFLES_2
    
    # Создаем файл для отправки
    filename = get_csv_filename(raffle_id, raffle.name)
    csv_file = InputFile(io.BytesIO(csv_content), filename=filename)
    
    try:
        await query.message.reply_document(
            document=csv_file,
            caption=f"📊 CSV файл с участниками розыгрыша: {raffle.name}"
        )
        await query.answer("✅ CSV файл отправлен", show_alert=True)
    except Exception as e:
        await query.answer(f"❌ Ошибка при отправке файла: {e}", show_alert=True)
    
    return STEP_RAFFLES_2