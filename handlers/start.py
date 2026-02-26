import sys
import os
from pathlib import Path

# Добавляем корневую директорию проекта в sys.path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from telegram import Update
from telegram.ext import ContextTypes
from keyboards.base_keyboards import get_start_keyboard, get_bot_menu, get_admin_keyboard, get_webapp_button, get_dashboard_keyboard

from database.db_session import get_db
from database.models import BotUser, Channel_tg, Raffle, ReferralLink
from datetime import datetime


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("=" * 50)
    print("START_COMMAND ВЫЗВАН!")
    print("=" * 50)
    try:
        if not update or not update.message:
            print("ОШИБКА: update или update.message отсутствует")
            return
            
        user = update.effective_user
        if not user:
            print("Ошибка: не удалось получить информацию о пользователе")
            return
        
        print(f"Получена команда /start от пользователя {user.id} (@{user.username})")
        
        # Проверяем наличие реферального параметра
        referral_code = None
        if update.message and update.message.text:
            text_parts = update.message.text.split()
            if len(text_parts) > 1:
                param = text_parts[1]
                if param.startswith('ref_'):
                    referral_code = param[4:]  # Убираем префикс "ref_"
                    print(f"Обнаружен реферальный код: {referral_code}")
        
        try:
            db = next(get_db())
            print("База данных подключена успешно")
        except Exception as db_error:
            print(f"ОШИБКА ПОДКЛЮЧЕНИЯ К БД: {db_error}")
            import traceback
            traceback.print_exc()
            try:
                await update.message.reply_text(
                    "⚠️ Ошибка подключения к базе данных. Попробуйте позже или обратитесь в поддержку.",
                    parse_mode='HTML'
                )
            except:
                pass
            return

        try:
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
                        f"Что вам доступно:\n"
                        f"📱 Telegram каналы: {channels_count}/10\n"
                        f"🎁 Активные розыгрыши: {active_raffles}/3\n"
                        f"🏆 Максимум победителей: 10\n"
                        f"✅ Автоматические розыгрыши\n"
                        f"✅ Реферальная система\n"
                        f"✅ Редактирование розыгрышей\n"
                        f"✅ Просмотр результатов розыгрыша\n"
                        f"✅ Скачивание CSV\n\n"
                        f"<b>Недоступно на вашей версии:</b>\n"
                        f"❌ Telegram каналы: 25\n"
                        f"❌ Активные розыгрыши: 20\n"
                        f"❌ Максимум победителей: не ограничено\n"
                        f"❌ Возможность самому выбирать победителя\n"
                        f"❌ Статистика в реальном времени по конкурсам\n\n"
                        f"💡 <b>Для расширения возможностей подключите расширенную версию бота!</b> 👇👇👇",
                        reply_markup=get_dashboard_keyboard(),
                        parse_mode='HTML'
                    )
                    
                    return

                # Если у пользователя есть запись, но каналов ещё нет — показываем приветствие
                await update.message.reply_text(
                    "👋 Добро пожаловать в бот для проведения розыгрышей в\n"
                    "Телеграмм каналах и группах!\n\n"
                    "✅ Для получения доступа к созданию розыгрышей добавьте свой\n"
                    "канал в систему.\n\n"
                    "✨ После добавления первого канала вы\n"
                    "автоматически получите доступ к функциям бота!",
                    reply_markup=get_start_keyboard(),
                    parse_mode='HTML'
                )
                
                return

            # Новый пользователь: создаём запись в БД и отправляем приветствие
            new_user = BotUser(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                version='basic',
                referral_tickets=0
            )

            try:
                db.add(new_user)
                db.flush()  # Получаем ID нового пользователя
                
                # Обрабатываем реферальную ссылку, если она есть
                if referral_code:
                    referral_link = db.query(ReferralLink).filter_by(
                        referral_code=referral_code,
                        is_used=False
                    ).first()
                    
                    if referral_link:
                        # Проверяем, что пользователь не приглашает сам себя
                        if referral_link.creator_id != user.id:
                            # Помечаем ссылку как использованную
                            referral_link.is_used = True
                            referral_link.used_by_id = user.id
                            referral_link.used_at = datetime.now()
                            
                            # Добавляем билет пригласившему пользователю
                            creator = db.query(BotUser).filter_by(
                                telegram_id=referral_link.creator_id
                            ).first()
                            
                            if creator:
                                creator.referral_tickets = (creator.referral_tickets or 0) + 1
                                print(f"Добавлен билет пользователю {creator.telegram_id}. Всего билетов: {creator.referral_tickets}")
                                
                                # Уведомляем пригласившего пользователя
                                try:
                                    from telegram import Bot
                                    import os
                                    bot_token = os.getenv('BOT_TOKEN')
                                    if bot_token:
                                        bot = Bot(token=bot_token)
                                        await bot.send_message(
                                            chat_id=creator.telegram_id,
                                            text=f"🎉 Ваш друг перешел по вашей реферальной ссылке!\n"
                                                 f"✅ Вам добавлен 1 билет.\n"
                                                 f"📊 Всего билетов: {creator.referral_tickets}",
                                            parse_mode='HTML'
                                        )
                                except Exception as notify_error:
                                    print(f"Ошибка при отправке уведомления: {notify_error}")
                            
                            db.commit()
                            print(f"Реферальная ссылка {referral_code} успешно использована")
                        else:
                            print(f"Пользователь пытается использовать свою собственную реферальную ссылку")
                    else:
                        print(f"Реферальная ссылка {referral_code} не найдена или уже использована")
                
                db.commit()
            except Exception as e:
                db.rollback()
                print("Ошибка при создании пользователя в /start:", e)
                import traceback
                traceback.print_exc()
                await update.message.reply_text(
                    "Произошла внутренняя ошибка. Попробуйте снова позже.",
                    parse_mode='HTML'
                )
                return

            # Приветственное сообщение для нового пользователя
            await update.message.reply_text(
                "👋 Добро пожаловать в бот для проведения розыгрышей в\n"
                "Телеграмм каналах и группах!\n\n"
                "✅ Для получения доступа к созданию розыгрышей добавьте свой\n"
                "канал в систему.\n\n"
                "✨ После добавления первого канала вы\n"
                "автоматически получите доступ к функциям бота!",
                reply_markup=get_start_keyboard(),
                parse_mode='HTML'
            )
        finally:
            # Закрываем сессию БД в конце
            db.close()
    
    except Exception as e:
        print(f"Ошибка в обработчике start_command: {e}")
        import traceback
        traceback.print_exc()
        try:
            await update.message.reply_text(
                "Произошла ошибка при обработке команды. Попробуйте еще раз или обратитесь в поддержку.",
                parse_mode='HTML'
            )
        except:
            pass

