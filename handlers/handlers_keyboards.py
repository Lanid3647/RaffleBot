
import time
import re
import json
from datetime import datetime

# Импорты из telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes, ConversationHandler

# Ваши утилиты
from utils.base_utils import (
    get_for_type_eight,
    get_for_type_nine,
    collect_raffle_data,
    generate_confirmation_text,
    get_final_confirmation_keyboard,
    get_for_type_ten,
    get_selected_count
)

# База данных
from database.db_session import get_db
from database.models import Raffle, Channel_tg

# Клавиатуры
from keyboards.base_keyboards import (
    get_keyboard_draw_1,
    get_time,
    get_referral,
    get_bot_menu_draw_1,
    get_bot_menu,
    get_bot_menu_draw_3
)

import  logging


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def add_channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    if context.user_data.get('adding_channel'):
        await query.message.reply_text(
            "Вы уже начали добавление канала — пожалуйста, пришлите ссылку на канал или отмените операцию (/cancel).",
            parse_mode='HTML'
        )
        return
    # Устанавливаем режим ожидания ссылки
    context.user_data['adding_channel'] = True
    context.user_data['adding_channel_ts'] = int(time.time())

    await query.message.delete()

    await query.message.reply_text(
        "📱 Добавление Telegram каналов\n\n"
        "📋 Инструкция:\n"
        "1. Добавьте бота в ваш канал/группу как администратора\n\n"
        "2. Выдайте боту права:\n"
        "• Отправка сообщений\n"
        "• Редактирование сообщений\n"
        "• Добавление пользователей\n\n"
        "3. Отправьте ссылку на канал в одном из форматов:\n"
        "• https://t.me/channel_name\n"
        "• @channel_name\n"
        "• ID канала (например: -1001234567890)\n\n"
        "📤 <b>Отправьте ссылку на канал:</b>",
        parse_mode='HTML'
    )

async def new_version(update: Update, context: ContextTypes.DEFAULT_TYPE):

        query = update.callback_query
        await query.answer()
        data = query.data

        if data == "get_new_version":
            await query.message.reply_text(
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
                f"✅Возможность самому выбирать победителя\n"
                f"✅Статистика в реальном времени по конкурсам\n\n"
                f"📞 Для подключения расширенной версии обратитесь:\n"
                f"👤 @XXXX\n",
                parse_mode='HTML'
            )


STEP_1, STEP_2, STEP_3, STEP_4, STEP_5, STEP_6, STEP_7, STEP_8, STEP_9, STEP_10, STEP_11, STEP_12 = range(12)

class RaffleCreator:
    def __init__(self):
        self.steps = {
            STEP_1: self.step_1,
            STEP_2: self.step_2,
            STEP_3: self.step_3,
            STEP_4: self.step_4,
            STEP_5: self.step_5,
            STEP_6: self.step_6,
            STEP_7: self.step_7,
            STEP_8: self.step_8,
            STEP_9: self.step_9,
            STEP_10: self.step_10,
            STEP_11: self.step_11,
            STEP_12: self.step_12
        }

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        context.user_data.clear()
        context.user_data['current_step'] = STEP_1
        context.user_data['step_data'] = {}
        context.user_data['message_ids'] = []

        return await self.show_step(update, context, STEP_1)

    async def show_step(self, update: Update, context: ContextTypes.DEFAULT_TYPE, step: int):
        await self.delete_previous_messages(update, context)

        result = await self.steps[step](update, context, is_showing=True)

        context.user_data['current_step'] = step

        return result

    async def handle_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        current_step = context.user_data.get('current_step', STEP_1)

        if update.message:
            text = update.message.text.strip()
            if text == "⬅️Назад":
                return await self.go_back(update, context)
            elif text == "❌Отменить создание":
                return await self.cancel(update, context)

        if current_step in self.steps:
            result = await self.steps[current_step](update, context, is_showing=False)
            return result

        return current_step

    async def handle_step_6(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отдельный обработчик для шага 6"""

        if update.message and update.message.text:
            text = update.message.text.strip()
            if text == "⬅️Назад":
                return await self.go_back(update, context)
            elif text == "❌Отменить создание":
                return await self.cancel(update, context)

        # Вызываем шаг 6
        return await self.step_6(update, context, is_showing=False)

    async def go_back(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Возврат на предыдущий шаг"""
        current_step = context.user_data.get('current_step', STEP_1)

        # Определяем предыдущий шаг
        if current_step > STEP_1:
            previous_step = current_step - 1
            return await self.show_step(update, context, previous_step)
        else:
            # Если это первый шаг, отменяем создание
            return await self.cancel(update, context)

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отмена создания розыгрыша"""
        # Удаляем все сообщения
        await self.delete_previous_messages(update, context)

        # Очищаем данные, но сохраняем флаг отмены
        context.user_data.clear()
        context.user_data['just_cancelled'] = True  # Флаг, что только что отменили

        # Показываем главное меню в одном сообщении, чтобы избежать проблем с обработкой
        reply_markup = get_bot_menu()
        await update.message.reply_text(
            "❌️ Создание розыгрыша отменено️\n\n⚡️️ Главное меню ⚡️️",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

        return ConversationHandler.END

    async def delete_previous_messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Удаляет предыдущие сообщения бота"""
        message_ids = context.user_data.get('message_ids', [])
        chat_id = update.effective_chat.id

        for msg_id in message_ids:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
            except:
                pass

        # Очищаем список
        context.user_data['message_ids'] = []

    def save_message_id(self, context: ContextTypes.DEFAULT_TYPE, message_id: int):
        """Сохраняет ID сообщения для последующего удаления"""
        if 'message_ids' not in context.user_data:
            context.user_data['message_ids'] = []
        context.user_data['message_ids'].append(message_id)

    async def handle_navigation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает только навигационные кнопки"""
        query = update.callback_query
        await query.answer()
        data = query.data

        if data == "back_to_previous_step":
            return await self.go_back(update, context)
        elif data == "cancel_creation":
            return await self.cancel(update, context)

        # Если это не навигация, возвращаем текущее состояние
        return context.user_data.get('current_step', STEP_1)


    # Шаг 1: Тип розыгрыша
    async def step_1(self, update: Update, context: ContextTypes.DEFAULT_TYPE, is_showing: bool):
        if is_showing:
            # Показываем шаг
            # Проверяем, есть ли у сообщения связь с ботом
            effective_message = update.effective_message
            chat_id = effective_message.chat.id
            
            # Если у сообщения нет связи с ботом, используем context.bot.send_message
            try:
                # Пробуем использовать reply_text
                msg1 = await effective_message.reply_text(
                    f"🤖 Шаг 1 из 12: Тип определения победителей\n\n",
                    reply_markup=get_bot_menu_draw_3(),
                    parse_mode='HTML'
                )
            except (RuntimeError, AttributeError):
                # Если не получилось, используем context.bot.send_message
                msg1 = await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"🤖 Шаг 1 из 12: Тип определения победителей\n\n",
                    reply_markup=get_bot_menu_draw_3(),
                    parse_mode='HTML'
                )
            self.save_message_id(context, msg1.message_id)

            try:
                msg2 = await effective_message.reply_text(
                    "Выберите способ определения победителей:\n\n"
                    "🤖 Автоматический - бот случайно выберет победителей\n"
                    "📋 Самостоятельный - вы получите таблицу для самостоятельного подведения\n",
                    reply_markup=get_keyboard_draw_1(),
                    parse_mode='HTML'
                )
            except (RuntimeError, AttributeError):
                # Если не получилось, используем context.bot.send_message
                msg2 = await context.bot.send_message(
                    chat_id=chat_id,
                    text="Выберите способ определения победителей:\n\n"
                         "🤖 Автоматический - бот случайно выберет победителей\n"
                         "📋 Самостоятельный - вы получите таблицу для самостоятельного подведения\n",
                    reply_markup=get_keyboard_draw_1(),
                    parse_mode='HTML'
                )
            self.save_message_id(context, msg2.message_id)

            return STEP_1

        # Обрабатываем ввод (выбор типа)
        if update.callback_query:
            query = update.callback_query
            await query.answer()

            # ✅ ВАЖНО: Проверяем, что кнопка существует
            print(f"Callback data: {query.data}")  # Для отладки

            if query.data == "type_auto":
                context.user_data['step_1'] = 'auto'
                # ✅ Удаляем сообщение с кнопками после выбора
                try:
                    await query.message.delete()
                    # Удаляем ID из списка, если он там есть
                    if query.message.message_id in context.user_data.get('message_ids', []):
                        context.user_data['message_ids'].remove(query.message.message_id)
                except:
                    pass

                return await self.show_step(update, context, STEP_2)

            elif query.data == "type_me":
                context.user_data['step_1'] = 'manual'
                await query.message.reply_text(
                    f"❌ Самостоятельные розыгрыши недоступны на вашей версии (Базовая)\n\n"
                    f"💡 Для доступа к этой функции подключите расширенную версию.\n\n"
                    f"📞 Для подключения расширенной версии обратитесь:\n"
                    f" 👤 @XXXX",
                    parse_mode='HTML'
                )

                return STEP_1


            else:
                # ✅ Если пришел неизвестный callback, остаемся на шаге 1
                print(f"Unknown callback data: {query.data}")
                return STEP_1

        return STEP_1

    # Шаг 2: Количество победителей
    async def step_2(self, update: Update, context: ContextTypes.DEFAULT_TYPE, is_showing: bool):
        if is_showing:
            msg = await update.effective_message.reply_text(
                f"🏆 Шаг 2 из 12: Количество победителей\n\n"
                f"Введите количество победителей (1-10):",
                reply_markup=get_bot_menu_draw_1(),
                parse_mode='HTML'
            )
            self.save_message_id(context, msg.message_id)
            return STEP_2

        # Обрабатываем ввод числа
        if update.message:
            text = update.message.text.strip()

            winners_count = int(update.message.text.strip())
            if 1 <= winners_count <= 100:
                context.user_data['step_2'] = winners_count

                return await self.show_step(update, context, STEP_3)
            else:
                await update.message.reply_text(
                    "❌ Введите число от 1 до 10",
                    parse_mode='HTML'
                )
                return STEP_2

        return STEP_2

    # Шаг 3: Название розыгрыша
    async def step_3(self, update: Update, context: ContextTypes.DEFAULT_TYPE, is_showing: bool):
        if is_showing:
            msg = await update.effective_message.reply_text(
                f"📝 Шаг 3 из 12: Служебное название\n\n"
                f"Введите служебное название розыгрыша:",
                reply_markup=get_bot_menu_draw_1(),
                parse_mode='HTML'
            )
            self.save_message_id(context, msg.message_id)
            return STEP_3

        if update.message:
            name = update.message.text.strip()
            if name:
                if 'step_data' not in context.user_data:

                    context.user_data['step_data'] = {}
                context.user_data['step_data'] ['step_3'] = name

                return await self.show_step(update, context, STEP_4)
            else:
                await update.message.reply_text(
                    "❌ Название не может быть пустым",
                    parse_mode='HTML'
                )
                return STEP_3

        return STEP_3

    # Шаг 4: Время начала
    async def step_4(self, update: Update, context: ContextTypes.DEFAULT_TYPE, is_showing: bool):
        if is_showing:
            msg1 = await update.effective_message.reply_text(
                f"⏰ Шаг 4 из 12: Время начала\n\n",
                reply_markup=get_bot_menu_draw_1(),
                parse_mode='HTML'
            )
            self.save_message_id(context, msg1.message_id)

            msg2 = await update.effective_message.reply_text(
                "⏳ Когда нужно опубликовать розыгрыш?",
                reply_markup=get_time(),
                parse_mode='HTML'
            )
            self.save_message_id(context, msg2.message_id)
            return STEP_4

        if update.callback_query:
            query = update.callback_query
            await query.answer()

            if query.data == "time_start":
                start_time = datetime.now()
                if 'step_data' not in context.user_data:
                    context.user_data['step_data'] = {}
                context.user_data['step_data']['step_4'] = start_time
                context.user_data['step_data']['start_now'] = True
                return await self.show_step(update, context, STEP_5)
            elif query.data == "time_end":
                msg = await query.message.reply_text(
                    "Введите время начала (ЧЧ:ММ ДД.ММ.ГГГГ):",
                    parse_mode='HTML'
                )
                self.save_message_id(context, msg.message_id)
                context.user_data['waiting_for_start_time'] = True
                return STEP_4

        if update.message and context.user_data.get('waiting_for_start_time'):
            text = update.message.text.strip()
            datetime_pattern = r'^(\d{1,2}):(\d{2})\s+(\d{1,2})\.(\d{1,2})\.(\d{4})$'
            match = re.match(datetime_pattern, text)

            if match:
                hour, minute, day, month, year = match.groups()
                try:
                    input_datetime = datetime(
                        year=int(year), month=int(month), day=int(day),
                        hour=int(hour), minute=int(minute)
                    )

                    if input_datetime > datetime.now():
                        if 'step_data' not in context.user_data:
                            context.user_data['step_data'] = {}
                        context.user_data['step_data']['step_4'] = input_datetime
                        context.user_data['step_data']['start_now'] = False
                        context.user_data['waiting_for_start_time'] = False
                        return await self.show_step(update, context, STEP_5)
                    else:
                        await update.message.reply_text(
                            "❌ Дата и время должны быть в будущем",
                            parse_mode='HTML'
                        )
                except ValueError as e:
                    await update.message.reply_text(
                        f"❌ Некорректная дата: {e}",
                        parse_mode='HTML'
                    )
            else:
                await update.message.reply_text(
                    "❌ Неверный формат. Используйте: ЧЧ:ММ ДД.ММ.ГГГГ",
                    parse_mode='HTML'
                )

        return STEP_4

    # Шаг 5: Время окончания (ваш type_six)
    async def step_5(self, update: Update, context: ContextTypes.DEFAULT_TYPE, is_showing: bool):
        if is_showing:
            # Получаем время начала для контекста
            start_time = context.user_data.get('step_data', {}).get('step_4')
            start_text = start_time.strftime('%d.%m.%Y %H:%M') if start_time else "не указано"

            msg = await update.effective_message.reply_text(
                f"⏰ Шаг 5 из 12: Время окончания\n\n"
                f"Введите время окончания розыгрыша в формате: чч:мм дд.мм.гггг:\n\n"
                f"Например: 15:30 25.12.2025\n"
                f"(время указывается по МСК)\n",
                reply_markup=get_bot_menu_draw_1(),
                parse_mode='HTML'
            )
            self.save_message_id(context, msg.message_id)
            return STEP_5

        # Обрабатываем ввод времени окончания
        if update.message:
            text = update.message.text.strip()
            datetime_pattern = r'^(\d{1,2}):(\d{2})\s+(\d{1,2})\.(\d{1,2})\.(\d{4})$'
            match = re.match(datetime_pattern, text)

            if match:
                hour, minute, day, month, year = match.groups()
                try:
                    end_datetime = datetime(
                        year=int(year), month=int(month), day=int(day),
                        hour=int(hour), minute=int(minute)
                    )
                    # Получаем время начала для контекста
                    # Проверяем, что время окончания позже времени начала
                    start_time = context.user_data.get('step_data', {}).get('step_4')

                    if start_time and end_datetime > start_time:
                        if 'step_data' not in context.user_data:
                            context.user_data['step_data'] = {}
                        context.user_data['step_data']['step_5'] = end_datetime

                        return await self.show_step(update, context, STEP_6)
                    else:
                        await update.message.reply_text(
                            "❌ Дата и время должны быть в будущем",
                            parse_mode='HTML'
                        )
                        return STEP_5
                except ValueError:
                    await update.message.reply_text(
                        "❌ Некорректная дата",
                        parse_mode='HTML'
                    )
                    return STEP_5
            else:
                await update.message.reply_text(
                    "❌ Неверный формат",
                    parse_mode='HTML'
                )
                return STEP_5

        return STEP_5

    # Шаг 6: Контент розыгрыша (исправленная версия)
    async def step_6(self, update: Update, context: ContextTypes.DEFAULT_TYPE, is_showing: bool):
        if is_showing:
            msg = await update.effective_message.reply_text(
                f"📝 Шаг 6 из 11: Текст и картинка (видео) для розыгрыша\n\n"
                f"✉️ Отправьте текст для розыгрыша. , который будет отображаться участникам.\n\n"
                f"Вы можете также отправить вместе с текстом\n"
                f"🖼 картинку, видео, GIF или Премиум🎆эмодзи,\n"
                f"а также пользоваться разметкой.\n\n"
                f"❗️ Вы можете использовать только 1 медиафайл.\n\n"
                f"💡 Поддерживается HTML разметка:\n"
                f"• жирный текст - <b>текст</b>\n"
                f"• курсив - <i>текст</i>\n"
                f"• подчеркнутый - <u>текст</u>\n"
                f"• ссылка - <a href='ссылка'>текст</a>\n"
                f"• копируемый по клику код - <code>текст</code>\n"
                f"• блок кода - <pre>текст</pre>\n",
                reply_markup=get_bot_menu_draw_1(),
                parse_mode='HTML'
            )
            self.save_message_id(context, msg.message_id)
            return STEP_6

            # Обрабатываем контент
        if update.message:
            message = update.message

            # Проверяем навигационные кнопки (если это текст)
            if message.text and message.text.strip() in ["⬅️Назад", "❌Отменить создание"]:
                return await self.handle_input(update, context)

            # Подготовим данные контента (как в вашем старом коде)
            content_data = {
                'text': '',
                'media_type': None,
                'media_file_id': None,
                'has_media': False
            }

            # ✅ ВАЖНО: Обработка как в вашем работающем коде
            # Только текст
            if message.text:
                content_data['text'] = message.text
                content_data['has_media'] = False

            # Текст + медиа или только медиа
            elif message.caption or (message.photo or message.video or message.animation or message.document):
                content_data['text'] = message.caption or ''
                content_data['has_media'] = True

                if message.photo:
                    content_data['media_type'] = 'photo'
                    content_data['media_file_id'] = message.photo[-1].file_id

                elif message.video:
                    content_data['media_type'] = 'video'
                    content_data['media_file_id'] = message.video.file_id

                elif message.animation:
                    content_data['media_type'] = 'animation'
                    content_data['media_file_id'] = message.animation.file_id

                elif message.document:
                    content_data['media_type'] = 'document'
                    content_data['media_file_id'] = message.document.file_id

            # Проверяем, что хоть что-то есть
            if not content_data['text'] and not content_data['has_media']:
                await message.reply_text(
                    "❌ Пожалуйста, отправьте текст или медиафайл для розыгрыша.",
                    parse_mode='HTML'
                )
                return STEP_6

            if 'step_data' not in context.user_data:
                context.user_data['step_data'] = {}
            context.user_data['step_data']['step_6'] = content_data


            # ✅ ВАЖНО: Возвращаем STEP_7 как в вашем работающем коде
            return await self.show_step(update, context, STEP_7)

        return STEP_6

        # ✅ Если не update.message, возвращаем STEP_6
        return STEP_6

    # Шаг 7: Реферальный бонус (ваш type_eight)
    async def step_7(self, update: Update, context: ContextTypes.DEFAULT_TYPE, is_showing: bool):
        if is_showing:
            msg1 = await update.effective_message.reply_text(
                f"👥 Шаг 7 из 12: Реферальный бонус\n\n",
                reply_markup=get_bot_menu_draw_1(),
                parse_mode='HTML'
            )
            self.save_message_id(context, msg1.message_id)
            msg2 = await update.effective_message.reply_text(
                f"За сколько приглашенных друзей давать пользователю +1 билет?\n\n"
                f"Выберите число от 0 до 5 (0 = отключить реферальную систему):\n",
                reply_markup=get_referral(),
                parse_mode='HTML'
            )
            self.save_message_id(context, msg2.message_id)
            return STEP_7

            # ⭐ ДОБАВЬТЕ ЭТО: Обработка текстовых сообщений (кнопки "Назад")
        if update.message and update.message.text:
            text = update.message.text.strip()
            if text == "⬅️Назад":
                return await self.go_back(update, context)
            elif text == "❌Отменить создание":
                return await self.cancel(update, context)


        # Обрабатываем выбор реферального бонуса
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            data = query.data

            if data.startswith("referral_"):
                referral_value = int(data.split("_")[1])
                if 'step_data' not in context.user_data:
                    context.user_data['step_data'] = {}

                context.user_data['step_data']['step_7'] = {
                    'referral_bonus_required': referral_value,
                    'referral_bonus_enable': referral_value > 0,
                    'referral_bonus_tickets': 1 if referral_value > 0 else 0
                }

                if referral_value == 0:
                    await query.edit_message_text(
                        "✅ Реферальная система отключена",
                        parse_mode='HTML'
                    )
                else:
                    await query.edit_message_text(
                        f"✅ За каждых {referral_value} приглашенных друзей +1 билет",
                        parse_mode='HTML'
                    )

                return await self.show_step(update, context, STEP_8)

        return STEP_7

    # Шаг 8: Выбор каналов публикации (ваш type_eight + handle_step_eight_actions)
    async def step_8(self, update: Update, context: ContextTypes.DEFAULT_TYPE, is_showing: bool):
        if is_showing:
            # Инициализируем список выбранных каналов (Telegram ID)
            if 'selected_publication_channels' not in context.user_data:
                context.user_data['selected_publication_channels'] = []

            selected_channels = context.user_data['selected_publication_channels']
            user_id = update.effective_user.id
            reply_markup = get_for_type_eight(user_id, selected_channels)

            msg1 = await update.effective_message.reply_text(
                f"📢 Шаг 8 из 12: Выбор каналов публикации\n\n",
                reply_markup=get_bot_menu_draw_1(),
                parse_mode='HTML'
            )
            self.save_message_id(context, msg1.message_id)

            msg2 = await update.effective_message.reply_text(
                f"Выберите каналы, в которых бот опубликует пост розыгрыша:\n\n"
                f"Эти каналы будут использоваться только для публикации поста розыгрыша и поста результатов.\n"
                f"В них не будет проверяться подписка.\n"
                f"Каналы для проверки подписки выберите на следующем шаге.\n\n"
                f"После выбора нажмите 'Продолжить':\n",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            self.save_message_id(context, msg2.message_id)
            return STEP_8

        if update.message and update.message.text:
            text = update.message.text.strip()
            if text == "⬅️Назад":
                return await self.go_back(update, context)
            elif text == "❌Отменить создание":
                return await self.cancel(update, context)

        # Обрабатываем действия с каналами
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            data = query.data

            if 'selected_publication_channels' not in context.user_data:
                context.user_data['selected_publication_channels'] = []

            selected_channels = context.user_data['selected_publication_channels']
            user_id = update.effective_user.id

            if data.startswith("select_channel_"):
                # 🔥 ИСПРАВЛЕНИЕ: Получаем Telegram ID канала как строку
                # data будет в формате: "select_channel_-1001234567890" или "select_channel_@username"
                channel_telegram_id = data.split("select_channel_")[1]

                print(f"DEBUG: Выбран channel_telegram_id: {channel_telegram_id}")
                print(f"DEBUG: Текущие выбранные: {selected_channels}")

                if channel_telegram_id in selected_channels:
                    selected_channels.remove(channel_telegram_id)
                    print(f"DEBUG: Удалили канал {channel_telegram_id}")
                else:
                    selected_channels.append(channel_telegram_id)
                    print(f"DEBUG: Добавили канал {channel_telegram_id}")

                reply_markup = get_for_type_eight(user_id, selected_channels)
                await query.edit_message_text(
                    f"Выбрано каналов: {len(selected_channels)}\n\n"
                    f"После выбора нажмите 'Продолжить':",
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
                return STEP_8

            elif data == "continue_to_next_step":
                if not selected_channels:
                    await query.answer("Выберите хотя бы один канал!", show_alert=True)
                    return STEP_8

                if 'step_data' not in context.user_data:
                    context.user_data['step_data'] = {}

                # ✅ Сохраняем Telegram ID выбранных каналов
                context.user_data['step_data']['step_8'] = selected_channels.copy()

                print(f"DEBUG: Сохранены каналы для публикации (Telegram ID): {selected_channels}")

                await query.edit_message_text(
                    f"✅ Выбрано {len(selected_channels)} каналов для публикации",
                    parse_mode='HTML'
                )
                return await self.show_step(update, context, STEP_9)

        return STEP_8

    # Шаг 9: Выбор каналов для подписки (ваш type_nine + handle_step_eight_actions_nine)
    async def step_9(self, update: Update, context: ContextTypes.DEFAULT_TYPE, is_showing: bool):
        if is_showing:
            # Инициализируем список выбранных каналов (Telegram ID)
            if 'selected_subscription_channels' not in context.user_data:
                # Берем Telegram ID из публикационных каналов
                publication_channels = context.user_data.get('selected_publication_channels', [])
                context.user_data['selected_subscription_channels'] = publication_channels.copy()

            selected_channels = context.user_data['selected_subscription_channels']
            user_id = update.effective_user.id
            reply_markup = get_for_type_nine(user_id, selected_channels)

            msg1 = await update.effective_message.reply_text(
                f"📦 Шаг 9 из 12: Выбор каналов для проверки подписки Телеграмм\n\n",
                reply_markup=get_bot_menu_draw_1(),
                parse_mode='HTML'
            )
            self.save_message_id(context, msg1.message_id)

            msg2 = await update.effective_message.reply_text(
                f"Пользователь должен будет подписаться на эти каналы для участия.\n"
                f"По умолчанию выбраны каналы публикации, но вы можете отключить, включить любые каналы для проверки подписки.\n\n"
                f"<b>Выбрано каналов:</b> {len(selected_channels)}\n\n"
                f"После выбора нажмите 'Сохранить':\n",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            self.save_message_id(context, msg2.message_id)

            return STEP_9

        if update.message and update.message.text:
            text = update.message.text.strip()
            if text == "⬅️Назад":
                return await self.go_back(update, context)
            elif text == "❌Отменить создание":
                return await self.cancel(update, context)

        # Обрабатываем действия с каналами
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            data = query.data

            if 'selected_subscription_channels' not in context.user_data:
                context.user_data['selected_subscription_channels'] = []

            selected_channels = context.user_data['selected_subscription_channels']
            user_id = update.effective_user.id

            if data.startswith("select_channel_"):
                # 🔥 ИСПРАВЛЕНИЕ: Получаем Telegram ID канала
                channel_telegram_id = data.split("select_channel_")[1]

                print(f"DEBUG Канал Telegram ID: {channel_telegram_id}")
                print(f"DEBUG До: {selected_channels}")

                if channel_telegram_id in selected_channels:
                    selected_channels.remove(channel_telegram_id)
                    print(f"DEBUG: Удалили канал {channel_telegram_id}")
                else:
                    selected_channels.append(channel_telegram_id)
                    print(f"DEBUG: Добавили канал {channel_telegram_id}")

                print(f"DEBUG После: {selected_channels}")

                reply_markup = get_for_type_nine(user_id, selected_channels)

                await query.edit_message_text(
                    f"Пользователь должен будет подписаться на эти каналы для участия.\n"
                    f"По умолчанию выбраны каналы публикации, но вы можете отключить, включить любые каналы для проверки подписки.\n\n"
                    f"<b>Выбрано каналов:</b> {len(selected_channels)}\n\n"
                    f"После выбора нажмите 'Сохранить':",
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
                return STEP_9

            elif data == "continue_to_next_step":
                if not selected_channels:
                    await query.answer("Выберите хотя бы один канал!", show_alert=True)
                    return STEP_9

                if 'step_data' not in context.user_data:
                    context.user_data['step_data'] = {}

                # ✅ Сохраняем Telegram ID каналов для подписки
                context.user_data['step_data']['step_9'] = selected_channels.copy()

                print(f"DEBUG: Сохранены каналы для подписки (Telegram ID): {selected_channels}")

                await query.edit_message_text(
                    f"✅ Выбрано {len(selected_channels)} каналов для проверки подписки",
                    parse_mode='HTML'
                )
                return await self.show_step(update, context, STEP_10)

        return STEP_9



    async def step_10(self, update: Update, context: ContextTypes.DEFAULT_TYPE, is_showing: bool):
        if is_showing:
            # Инициализируем состояния буста и капчи (как в шаге 9 для каналов)
            if 'luck_boost_enabled' not in context.user_data:
                context.user_data['luck_boost_enabled'] = False
            if 'captcha_enabled' not in context.user_data:
                context.user_data['captcha_enabled'] = False

            user_id = update.effective_user.id
            reply_markup = get_for_type_ten(user_id, context)

            msg1 = await update.effective_message.reply_text(
                f"✨ Шаг 10 из 12: Дополнительные опции\n\n",
                reply_markup=get_bot_menu_draw_1(),
                parse_mode='HTML'
            )
            self.save_message_id(context, msg1.message_id)

            msg2 = await update.effective_message.reply_text(
                f"Выберите дополнительные опции:\n\n"
                f"🎯 <b>Буст на удачу</b> - увеличивает шансы на победу\n"
                f"🔐 <b>Капча</b> - защита от ботов\n\n"
                f"Нажмите на кнопку, чтобы включить/выключить опцию.\n"
                f"После выбора нажмите 'Сохранить':",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            self.save_message_id(context, msg2.message_id)

            return STEP_10

        # ⭐ Обработка текстовых сообщений (кнопки "Назад")
        if update.message and update.message.text:
            text = update.message.text.strip()
            if text == "⬅️Назад":
                return await self.go_back(update, context)
            elif text == "❌Отменить создание":
                return await self.cancel(update, context)

        # ⭐ Обработка действий с кнопками (точно как в шаге 9)
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            data = query.data

            # Обработка кнопок буста и капчи
            if data == "toggle_boost":
                # Переключаем буст
                context.user_data['luck_boost_enabled'] = not context.user_data['luck_boost_enabled']
                user_id = update.effective_user.id
                # Обновляем сообщение (как в шаге 9)
                reply_markup = get_for_type_ten(user_id, context)
                await query.edit_message_text(
                    f"Выбрано опций: {get_selected_count(context)}\n\n"
                    f"После выбора нажмите 'Сохранить':",
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
                return STEP_10

            elif data == "toggle_captcha":
                # Переключаем капчу
                context.user_data['captcha_enabled'] = not context.user_data['captcha_enabled']

                user_id = update.effective_user.id
                # Обновляем сообщение (как в шаге 9)
                reply_markup = get_for_type_ten(user_id, context)
                await query.edit_message_text(
                    f"Выбрано опций: {get_selected_count(context)}\n\n"
                    f"После выбора нажмите 'Сохранить':",
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
                return STEP_10

            elif data == "save_options":
                if 'step_data' not in context.user_data:
                    context.user_data['step_data'] = {}

                context.user_data['step_data']['step_10'] = {
                    'luck_boost_enabled': context.user_data['luck_boost_enabled'],
                    'captcha_enabled': context.user_data['captcha_enabled']
                }

                # Сообщение о сохранении
                await query.edit_message_text(
                    f"✅ Дополнительные опции сохранены!\n"
                    f"• Буст на удачу: {'✅' if context.user_data['luck_boost_enabled'] else '❌'}\n"
                    f"• Капча: {'✅' if context.user_data['captcha_enabled'] else '❌'}",
                    parse_mode='HTML'
                )

                # Переходим к шагу 11
                return await self.show_step(update, context, STEP_11)

        return STEP_10


    async def step_11(self, update: Update, context: ContextTypes.DEFAULT_TYPE, is_showing: bool):
        if is_showing:

            # Собираем все данные
            raffle_data = collect_raffle_data(context)

            # Создаем текст подтверждения
            confirmation_text = generate_confirmation_text(raffle_data, context)

            # Создаем клавиатуру
            reply_markup = get_final_confirmation_keyboard(
                luck_boost_enabled=context.user_data['luck_boost_enabled'],
                captcha_enabled=context.user_data['captcha_enabled']
            )

            msg1 = await update.effective_message.reply_text(
                f"✅Шаг 11 из 12: Финальное подтверждение\n",
                reply_markup=get_bot_menu_draw_1(),
                parse_mode='HTML'
            )
            self.save_message_id(context, msg1.message_id)

            msg2 = await update.effective_message.reply_text(
                confirmation_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            self.save_message_id(context, msg2.message_id)
            return STEP_11

        # ⭐ ДОБАВЬТЕ ЭТО: Обработка текстовых сообщений (кнопки "Назад")
        if update.message and update.message.text:
            text = update.message.text.strip()
            if text == "⬅️Назад":
                return await self.go_back(update, context)
            elif text == "❌Отменить создание":
                return await self.cancel(update, context)

        # Обрабатываем действия подтверждения
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            data = query.data

            if data == "toggle_luck_boost":
                context.user_data['luck_boost_enabled'] = not context.user_data.get('luck_boost_enabled', False)
                raffle_data = collect_raffle_data(context)
                confirmation_text = generate_confirmation_text(raffle_data, context)
                reply_markup = get_final_confirmation_keyboard(
                    luck_boost_enabled=context.user_data['luck_boost_enabled'],
                    captcha_enabled=context.user_data.get('captcha_enabled', False)
                )
                await query.edit_message_text(
                    text=confirmation_text,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
                return STEP_11

            elif data == "toggle_captcha":
                context.user_data['captcha_enabled'] = not context.user_data.get('captcha_enabled', False)
                raffle_data = collect_raffle_data(context)
                confirmation_text = generate_confirmation_text(raffle_data, context)
                reply_markup = get_final_confirmation_keyboard(
                    luck_boost_enabled=context.user_data.get('luck_boost_enabled', False),
                    captcha_enabled=context.user_data['captcha_enabled']
                )
                await query.edit_message_text(
                    text=confirmation_text,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
                return STEP_11


            elif data == "save_raffle":

                # ✅ Редактируем текущее сообщение
                await query.edit_message_text(
                    "💾 Сохраняем розыгрыш...",
                    parse_mode='HTML'
                )

                # Сохраняем ID сообщения шага 11 для удаления
                message_ids = context.user_data.get('message_ids', [])
                print(f"📋 Сохраненные message_ids перед сохранением: {message_ids}")

                success = await self.save_final_raffle(context, update)

                if success:
                    # ✅ Удаляем сообщения шага 11
                    chat_id = update.effective_chat.id

                    # Удаляем все сообщения из списка
                    for msg_id in message_ids:
                        try:
                            await context.bot.delete_message(
                                chat_id=chat_id,
                                message_id=msg_id
                            )
                            print(f"✅ Удалено сообщение с ID: {msg_id}")
                        except Exception as e:
                            print(f"⚠️ Не удалось удалить сообщение {msg_id}: {e}")

                    # Очищаем message_ids после удаления
                    context.user_data['message_ids'] = []

                    # Переходим к шагу 12
                    return await self.show_step(update, context, STEP_12)
                else:
                    await query.answer("❌ Ошибка при сохранении", show_alert=True)
                    return STEP_11

    async def step_12(self, update: Update, context: ContextTypes.DEFAULT_TYPE, is_showing: bool):
        if is_showing:
            import asyncio

            # 🔄 ИСПРАВЛЕНИЕ: Получаем ID розыгрыша из context.user_data
            raffle_id = context.user_data.get('saved_raffle_id')

            db = None
            try:
                if not raffle_id:
                    # Если ID нет в context, попробуем найти последний розыгрыш пользователя
                    db = next(get_db())
                    raffle = db.query(Raffle).filter_by(
                        owner_id=update.effective_user.id
                    ).order_by(Raffle.created_at.desc()).first()

                    if not raffle:
                        await update.effective_message.reply_text(
                            "❌ Ошибка: розыгрыш не найден в базе данных",
                            reply_markup=get_bot_menu(),
                            parse_mode='HTML'
                        )
                        return ConversationHandler.END
                    raffle_id = raffle.id
                    db.close()
                    db = None

                db = next(get_db())
                raffle = db.query(Raffle).filter_by(id=raffle_id).first()

                if not raffle:
                    await update.effective_message.reply_text(
                        "❌ Ошибка: розыгрыш не найден в базе данных",
                        reply_markup=get_bot_menu(),
                        parse_mode='HTML'
                    )
                    return ConversationHandler.END

                publication_channels = []

                # 🔥 ОТЛАДКА: Проверяем, что сохранено в БД
                print(f"🔍 DEBUG step_12:")
                print(f"  raffle.publication_channels (raw): {raffle.publication_channels}")
                print(f"  raffle.publication_channels (type): {type(raffle.publication_channels)}")
                print(f"  raffle.publication_channels (repr): {repr(raffle.publication_channels)}")

                if raffle.publication_channels:
                    try:
                        # Пробуем распарсить как JSON
                        if isinstance(raffle.publication_channels, str):
                            publication_channels = json.loads(raffle.publication_channels)
                        elif isinstance(raffle.publication_channels, list):
                            # Если уже список, используем как есть
                            publication_channels = raffle.publication_channels
                        else:
                            # Пробуем через ast.literal_eval для Python-списков в строке
                            import ast
                            if isinstance(raffle.publication_channels, str):
                                publication_channels = ast.literal_eval(raffle.publication_channels)
                            else:
                                publication_channels = []
                        
                        if not isinstance(publication_channels, list):
                            print(f"⚠️ publication_channels не является списком: {type(publication_channels)}")
                            publication_channels = []
                    except Exception as e:
                        print(f"❌ Ошибка парсинга каналов: {e}")
                        import traceback
                        traceback.print_exc()
                        publication_channels = []
                else:
                    print(f"⚠️ raffle.publication_channels пустое или None")

                print(f"📢 Каналы для публикации (после парсинга): {publication_channels}")
                print(f"📢 Количество каналов: {len(publication_channels)}")

                # Определяем время окончания
                end_time = raffle.end_date
                if end_time and isinstance(end_time, datetime):
                    end_time_str = end_time.strftime("%d.%m.%Y %H:%M")
                else:
                    end_time_str = "не указано"

                msg1 = await update.effective_message.reply_text(
                    f"🔄 Создание розыгрыша и публикация в каналах...\n\n",
                    parse_mode='HTML'
                )
                self.save_message_id(context, msg1.message_id)

                publication_results = []
                channel_messages_dict = {}  # Словарь для хранения message_id постов

                if publication_channels:
                    print(f"🔄 Начинаем публикацию в {len(publication_channels)} каналов...")
                    for channel_id in publication_channels:
                        try:
                            print(f"  📤 Публикация в канал {channel_id}...")
                            message = await publish_giveaway_to_channel(
                                raffle_id=raffle_id,
                                channel_id=str(channel_id),
                                bot=context.bot,
                                db_session=db
                            )
                            channel = db.query(Channel_tg).filter_by(channel_id=str(channel_id)).first()
                            channel_name = channel.channel_name if channel else f"Канал {channel_id}"

                            if message:
                                print(f"  ✅ Успешно опубликовано в {channel_name} (message_id: {message.message_id})")
                                publication_results.append({
                                    'success': True,
                                    'channel_name': channel_name,
                                    'message_id': message.message_id,
                                    'error': None
                                })
                                # Сохраняем message_id для обновления поста после завершения
                                channel_messages_dict[str(channel_id)] = message.message_id
                            else:
                                print(f"  ❌ Не удалось опубликовать в {channel_name}")
                                publication_results.append({
                                    'success': False,
                                    'channel_name': channel_name,
                                    'message_id': None,
                                    'error': 'Не удалось опубликовать'
                                })

                        except Exception as e:
                            print(f"  ❌ Ошибка при публикации в канал {channel_id}: {e}")
                            import traceback
                            traceback.print_exc()
                            publication_results.append({
                                'success': False,
                                'channel_name': f"Канал {channel_id}",
                                'message_id': None,
                                'error': str(e)
                            })
                else:
                    print(f"⚠️ Нет каналов для публикации (publication_channels пустой)")
                    publication_results = []
                
                # Сохраняем message_id постов в БД
                if channel_messages_dict:
                    raffle = db.query(Raffle).filter_by(id=raffle_id).first()
                    if raffle:
                        raffle.channel_messages = json.dumps(channel_messages_dict)
                        db.commit()
                        print(f"✅ Сохранены message_id постов: {channel_messages_dict}")

                # Формируем отчет о публикации
                success_count = len([r for r in publication_results if r['success']])
                total_count = len(publication_results)

                if success_count > 0:
                    status_text = f"✅ Розыгрыш успешно опубликован в {success_count} каналах!"
                elif total_count > 0:
                    status_text = "⚠️ Розыгрыш создан, но не опубликован в каналах"
                else:
                    status_text = "⚠️ Розыгрыш создан, но каналы для публикации не указаны"

                publication_text = "📊 Результаты публикации:\n"
                if publication_results:
                    for result in publication_results:
                        if result['success']:
                            publication_text += f"✅ {result['channel_name']}: опубликовано\n"
                        else:
                            publication_text += f"❌ {result['channel_name']}: ошибка - {result['error']}\n"
                else:
                    publication_text += "❌ Каналы для публикации не были указаны при создании розыгрыша\n"

                msg2 = await update.effective_message.reply_text(
                    f"{status_text}\n\n"
                    f"{publication_text}\n"
                    f"🎯 Успешно: {success_count}/{total_count if total_count > 0 else len(publication_channels)} каналов\n\n"
                    f"📋 Название: {raffle.name}\n"
                    f"⏰ Время окончания: {end_time_str}\n"
                    f"🔗 ID розыгрыша: {raffle_id}\n\n"
                    f"<i>Розыгрыш будет автоматически завершен в указанное время</i>",
                    reply_markup=get_bot_menu(),
                    parse_mode='HTML'
                )
                self.save_message_id(context, msg2.message_id)

                # ✅ Очищаем оставшиеся данные
                final_keys_to_remove = ['saved_raffle_id', 'message_ids', 'channel_message_ids']
                for key in final_keys_to_remove:
                    if key in context.user_data:
                        del context.user_data[key]

                return ConversationHandler.END
            finally:
                if db:
                    db.close()

        # После показа завершаем диалог
        return ConversationHandler.END



    async def save_final_raffle(self, context: ContextTypes.DEFAULT_TYPE, update: Update) -> bool:
        """Финальное сохранение розыгрыша в базу данных"""

        try:
            from database.db_session import get_db
            from database.models import Raffle, BotUser, Channel_tg
            import json
            from datetime import datetime

            user_id = update.effective_user.id
            step_data = context.user_data.get('step_data', {})

            db = next(get_db())
            bot_user = db.query(BotUser).filter_by(telegram_id=user_id).first()

            if not bot_user:
                print(f"Пользователь {user_id} не найден в базе")
                return False

            # Собираем данные
            winner_type_data = context.user_data.get('step_1', 'auto')
            winner_type = 'auto' if winner_type_data == 'auto' else 'manual'

            winners_count = context.user_data.get('step_2', 1)
            name = step_data.get('step_3', 'Без названия')
            start_date = step_data.get('step_4')
            end_date = step_data.get('step_5')

            content_data = step_data.get('step_6', {})
            media_caption = content_data.get('text', '')
            media_type = content_data.get('media_type')
            media_file_id = content_data.get('media_file_id')

            referral_data = step_data.get('step_7', {})
            referral_bonus_enable = referral_data.get('referral_bonus_enable', False)
            referral_bonus_tickets = referral_data.get('referral_bonus_tickets', 0)
            referral_bonus_required = referral_data.get('referral_bonus_required', 1)

            # 🔥 ВАЖНОЕ ИЗМЕНЕНИЕ: Теперь step_8 и step_9 содержат Telegram ID каналов
            publication_channels = step_data.get('step_8', [])  # Список Telegram ID каналов для публикации
            subscription_channels = step_data.get('step_9', [])  # Список Telegram ID каналов для подписки

            # 🔥 Проверяем, что каналы существуют в базе
            if publication_channels:
                print("Проверяем существование публикационных каналов в БД:")
                for channel_id in publication_channels:
                    channel = db.query(Channel_tg).filter_by(channel_id=str(channel_id), owner_id=bot_user.id).first()
                    if channel:
                        print(f"  ✓ Канал {channel_id} найден: {channel.channel_name or channel.channel_id}")
                    else:
                        print(f"  ✗ Канал {channel_id} НЕ найден в БД пользователя!")

            step_10_data = step_data.get('step_10', {})
            luck_boost_enabled = step_10_data.get('luck_boost_enabled', False)
            captcha_enabled = step_10_data.get('captcha_enabled', False)

            # Определяем статус
            current_time = datetime.now()
            if start_date and end_date:
                if start_date <= current_time <= end_date:
                    status = 'active'
                elif current_time < start_date:
                    status = 'pending'
                else:
                    status = 'completed'
            else:
                status = 'active'  # Если даты не указаны

            # 🔥 ВАЖНО: Сохраняем Telegram ID каналов как JSON строку
            publication_channels_json = json.dumps(publication_channels, ensure_ascii=False) if publication_channels else None
            subscription_channels_json = json.dumps(subscription_channels, ensure_ascii=False) if subscription_channels else None
            
            # 🔥 ОТЛАДКА: Проверяем, что сохраняем
            print(f"🔍 DEBUG save_final_raffle:")
            print(f"  publication_channels (list): {publication_channels}")
            print(f"  publication_channels (JSON): {publication_channels_json}")
            print(f"  subscription_channels (list): {subscription_channels}")
            print(f"  subscription_channels (JSON): {subscription_channels_json}")

            # Создаем розыгрыш
            raffle = Raffle(
                owner_id=bot_user.telegram_id,
                name=name,
                winner_type=winner_type,
                winners_count=winners_count,
                start_date=start_date,
                end_date=end_date,
                status=status,

                media_type=media_type,
                media_file_id=media_file_id,
                media_caption=media_caption,

                referral_bonus_enable=referral_bonus_enable,
                referral_bonus_tickets=referral_bonus_tickets,
                referral_bonus_required=referral_bonus_required,

                publication_channels=publication_channels_json,
                subscription_channels=subscription_channels_json,

                luck_boost_enabled=luck_boost_enabled,
                captcha_enabled=captcha_enabled,

                created_at=datetime.now()
            )

            db.add(raffle)
            db.commit()

            # 🔄 ВАЖНО: Получаем ID сохраненного розыгрыша
            db.refresh(raffle)
            saved_raffle_id = raffle.id

            # 🔥 ОТЛАДКА: Проверяем, что сохранилось в БД
            saved_raffle = db.query(Raffle).filter_by(id=saved_raffle_id).first()
            if saved_raffle:
                print(f"🔍 Проверка сохраненного розыгрыша:")
                print(f"  saved_raffle.publication_channels: {saved_raffle.publication_channels}")
                print(f"  saved_raffle.subscription_channels: {saved_raffle.subscription_channels}")

            print(f"✅ Розыгрыш сохранен: ID={saved_raffle_id}, Название='{name}'")
            print(f"=== END DEBUG ===")



            # ⚠️ ВАЖНО: Сохраняем ID розыгрыша перед очисткой других данных
            context.user_data['saved_raffle_id'] = saved_raffle_id

            # ⚠️ ВАЖНО: Не очищаем message_ids здесь, они нужны для шага 12
            # Но очищаем временные списки выбранных каналов
            keys_to_remove = [
                'step_1', 'step_2', 'step_data',
                'selected_publication_channels', 'selected_subscription_channels',
                'luck_boost_enabled', 'captcha_enabled',
                'waiting_for_start_time', 'current_step'
                # 'message_ids' - НЕ УДАЛЯЕМ! (нужны для шага 12)
                # 'saved_raffle_id' - НЕ УДАЛЯЕМ! (нужен для шага 12)
            ]

            for key in keys_to_remove:
                if key in context.user_data:
                    del context.user_data[key]

            # 🔥 Дополнительно: Сохраняем информацию о каналах для публикации
            # Это может пригодиться в шаге 12
            context.user_data['publication_channels_info'] = {
                'raffle_id': saved_raffle_id,
                'channels': publication_channels,
                'channel_names': []
            }



            # Получаем имена каналов для отчета
            for channel_id in publication_channels:
                channel = db.query(Channel_tg).filter_by(channel_id=str(channel_id), owner_id=bot_user.id).first()
                if channel:
                    context.user_data['publication_channels_info']['channel_names'].append(
                        channel.channel_name or channel.channel_id
                    )
                else:
                    context.user_data['publication_channels_info']['channel_names'].append(
                        f"Канал {channel_id}"
                    )

            return True

        except Exception as e:
            print(f"❌ Ошибка при сохранении розыгрыша: {e}")
            import traceback
            traceback.print_exc()
            if 'db' in locals():
                db.rollback()
            return False


async def publish_giveaway_to_channel(raffle_id: int, channel_id: str, bot, db_session):
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

    try:
        raffle = db_session.query(Raffle).filter(Raffle.id == raffle_id).first()

        if not raffle:
            return None

        post_text = f"Розыгрыш: {raffle.name}\n\n"

        if raffle.media_caption:
            post_text += f"{raffle.media_caption}\n\n"

        if raffle.end_date:
            end_str = raffle.end_date.strftime("%d.%m.%Y %H:%M")
            post_text += f"⏳ Завершится: {end_str}"

        # Получаем имя бота из переменных окружения
        import os
        bot_username = os.getenv('BOT_USERNAME', '')
        if not bot_username:
            # Пытаемся получить через API
            try:
                bot_info = await bot.get_me()
                bot_username = bot_info.username
            except:
                bot_username = 'your_bot_username'
        
        # 🔥 ВАЖНО: В каналах нельзя использовать WebApp кнопки, только URL кнопки
        # WebApp кнопки работают только в личных чатах с ботом
        # Поэтому всегда используем URL кнопку для каналов
        keyboard = [
            [
                InlineKeyboardButton(
                    text="🎁 Участвовать",
                    url=f"https://t.me/{bot_username}?start=raffle_{raffle_id}"
                )
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        # Публикуем обычным send_message / send_photo / send_video
        if raffle.media_type == 'photo' and raffle.media_file_id:
            return await bot.send_photo(
                chat_id=channel_id,
                photo=raffle.media_file_id,
                caption=post_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        elif raffle.media_type == 'video' and raffle.media_file_id:
            return await bot.send_video(
                chat_id=channel_id,
                video=raffle.media_file_id,
                caption=post_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        else:
            return await bot.send_message(
                chat_id=channel_id,
                text=post_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )

    except Exception as e:
        print(f"❌ Ошибка публикации: {e}")
        import traceback
        traceback.print_exc()
        return None

