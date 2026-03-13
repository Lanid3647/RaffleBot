"""
Модуль для автоматического завершения розыгрышей и выбора победителей
"""
import asyncio
import json
from datetime import datetime
from sqlalchemy.orm import Session
from database.db_session import get_db
from database.models import Raffle, Participant, BotUser, Ticket
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
import os
from dotenv import load_dotenv
import random
import logging

load_dotenv()
logger = logging.getLogger(__name__)


async def check_and_complete_raffles():
    """Проверяет и завершает розыгрыши, у которых истекло время"""
    db = None
    try:
        db = next(get_db())
        
        # Проверяем наличие новых полей в БД
        try:
            # Пробуем выполнить простой запрос с новыми полями
            test_query = db.query(Raffle.id).first()
        except Exception as e:
            if 'channel_messages' in str(e) or 'winners_selected' in str(e) or 'completed_at' in str(e):
                logger.warning("⚠️ Новые поля не найдены в БД. Примените миграцию: python migrations/add_new_fields.py")
                logger.warning("Планировщик будет пропускать проверку до применения миграции.")
                return
            raise
        
        # Находим активные розыгрыши, у которых истекло время
        now = datetime.now()
        
        # Используем более безопасный запрос, который работает даже без новых полей
        try:
            expired_raffles = db.query(Raffle).filter(
                Raffle.status == 'active',
                Raffle.end_date <= now
            ).all()
            
            # Фильтруем в Python, если поле winners_selected существует
            if hasattr(Raffle, 'winners_selected'):
                expired_raffles = [r for r in expired_raffles if not getattr(r, 'winners_selected', False)]
        except Exception as e:
            logger.error(f"Ошибка при запросе розыгрышей: {e}")
            return
        
        if not expired_raffles:
            return
        
        bot_token = os.getenv('BOT_TOKEN')
        if not bot_token:
            logger.error("BOT_TOKEN не найден")
            return
        
        bot = Bot(token=bot_token)
        
        for raffle in expired_raffles:
            try:
                await complete_raffle(raffle, bot, db)
            except Exception as e:
                logger.error(f"Ошибка при завершении розыгрыша {raffle.id}: {e}")
                import traceback
                traceback.print_exc()
                continue
    except Exception as e:
        logger.error(f"Ошибка в check_and_complete_raffles: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if db:
            db.close()


async def complete_raffle(raffle: Raffle, bot: Bot, db: Session):
    """Завершает розыгрыш: выбирает победителей, обновляет посты, отправляет уведомления"""
    try:
        # Выбираем победителей
        winners = await select_winners(raffle.id, raffle.winners_count, db)
        
        # Обновляем статус розыгрыша
        raffle.status = 'completed'
        raffle.winners_selected = True
        raffle.completed_at = datetime.now()
        db.commit()
        
        # Обновляем посты в каналах
        await update_channel_posts(raffle, winners, bot)
        
        # Отправляем уведомления
        await notify_raffle_completion(raffle, winners, bot, db)
        
        logger.info(f"Розыгрыш {raffle.id} успешно завершен")
        
    except Exception as e:
        logger.error(f"Ошибка при завершении розыгрыша {raffle.id}: {e}")
        db.rollback()
        raise


async def select_winners(raffle_id: int, winners_count: int, db: Session) -> list:
    """Выбирает победителей розыгрыша на основе билетов"""
    try:
        # Получаем всех участников розыгрыша
        participants = db.query(Participant).filter_by(raffle_id=raffle_id).all()
        
        if not participants:
            logger.warning(f"Нет участников в розыгрыше {raffle_id}")
            return []
        
        # Создаем список билетов для каждого участника
        tickets_pool = []
        participant_tickets = {}  # Словарь для хранения количества билетов каждого участника
        
        for participant in participants:
            # Получаем количество билетов участника
            tickets = db.query(Ticket).filter_by(
                user_id=participant.user_id
            ).count()
            
            # Используем tickets_count из Participant, если он есть
            if participant.tickets_count and participant.tickets_count > 0:
                tickets = participant.tickets_count
            
            # Минимум 1 билет на участника
            tickets = max(1, tickets)
            participant_tickets[participant.id] = tickets
            
            # Добавляем билеты участника в пул (пропорционально количеству билетов)
            for _ in range(tickets):
                tickets_pool.append(participant.id)
        
        if not tickets_pool:
            logger.warning(f"Пустой пул билетов для розыгрыша {raffle_id}")
            return []
        
        # Выбираем победителей случайным образом (взвешенная выборка)
        unique_participants = list(set(tickets_pool))
        winners_count = min(winners_count, len(unique_participants))
        
        if winners_count == 0:
            return []
        
        # Выбираем победителей
        winner_ids = random.sample(unique_participants, winners_count)
        
        # Отмечаем победителей в БД
        winners = []
        for winner_id in winner_ids:
            participant = db.query(Participant).filter_by(id=winner_id).first()
            if participant:
                participant.is_winner = True
                winners.append(participant)
        
        db.commit()
        logger.info(f"Выбрано {len(winners)} победителей для розыгрыша {raffle_id}")
        return winners
        
    except Exception as e:
        logger.error(f"Ошибка при выборе победителей для розыгрыша {raffle_id}: {e}")
        import traceback
        traceback.print_exc()
        if db:
            db.rollback()
        return []


async def update_channel_posts(raffle: Raffle, winners: list, bot: Bot):
    """Обновляет посты в каналах с результатами розыгрыша"""
    try:
        if not raffle.channel_messages:
            return
        
        # Парсим JSON с message_id постов
        channel_messages = json.loads(raffle.channel_messages)
        
        # Формируем текст с результатами
        results_text = f"🎉 Розыгрыш завершен!\n\n"
        results_text += f"🏷 Название: {raffle.name}\n\n"
        
        if winners:
            results_text += f"🏆 Победители:\n"
            for i, winner in enumerate(winners, 1):
                username = winner.username or f"ID: {winner.user_id}"
                results_text += f"{i}. @{username}\n"
        else:
            results_text += "❌ Победители не выбраны (не было участников)\n"
        
        # Обновляем посты в каждом канале
        for channel_id, message_id in channel_messages.items():
            try:
                # Формируем новую клавиатуру
                keyboard = [
                    [InlineKeyboardButton(
                        text="🔒 Розыгрыш завершен",
                        callback_data="raffle_completed"
                    )]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Обновляем сообщение
                if raffle.media_type == 'photo' and raffle.media_file_id:
                    await bot.edit_message_caption(
                        chat_id=channel_id,
                        message_id=message_id,
                        caption=results_text,
                        reply_markup=reply_markup,
                        parse_mode='HTML'
                    )
                elif raffle.media_type == 'video' and raffle.media_file_id:
                    await bot.edit_message_caption(
                        chat_id=channel_id,
                        message_id=message_id,
                        caption=results_text,
                        reply_markup=reply_markup,
                        parse_mode='HTML'
                    )
                else:
                    await bot.edit_message_text(
                        chat_id=channel_id,
                        message_id=message_id,
                        text=results_text,
                        reply_markup=reply_markup,
                        parse_mode='HTML'
                    )
            except Exception as e:
                logger.error(f"Ошибка при обновлении поста в канале {channel_id}: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Ошибка при обновлении постов в каналах: {e}")


async def notify_raffle_completion(raffle: Raffle, winners: list, bot: Bot, db: Session):
    """Отправляет уведомления создателю и победителям"""
    try:
        # Уведомление создателю
        owner = db.query(BotUser).filter_by(telegram_id=raffle.owner_id).first()
        if owner:
            owner_text = f"🎉 Розыгрыш завершен!\n\n"
            owner_text += f"🏷 Название: {raffle.name}\n"
            owner_text += f"👥 Участников: {len(db.query(Participant).filter_by(raffle_id=raffle.id).all())}\n"
            owner_text += f"🏆 Победителей: {len(winners)}\n\n"
            
            if winners:
                owner_text += "Победители:\n"
                for i, winner in enumerate(winners, 1):
                    username = winner.username or f"ID: {winner.user_id}"
                    owner_text += f"{i}. @{username}\n"
            
            try:
                await bot.send_message(
                    chat_id=owner.telegram_id,
                    text=owner_text,
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления создателю: {e}")
        
        # Уведомления победителям
        for winner in winners:
            try:
                user = db.query(BotUser).filter_by(telegram_id=winner.user_id).first()
                if user:
                    winner_text = f"🎉 Поздравляем! Вы победили в розыгрыше!\n\n"
                    winner_text += f"🏷 Название: {raffle.name}\n"
                    winner_text += f"👤 Свяжитесь с организатором для получения приза."
                    
                    await bot.send_message(
                        chat_id=user.telegram_id,
                        text=winner_text,
                        parse_mode='HTML'
                    )
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления победителю {winner.user_id}: {e}")
                
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомлений: {e}")


async def start_scheduler():
    """Запускает планировщик проверки розыгрышей"""
    logger.info("Планировщик розыгрышей запущен")
    consecutive_errors = 0
    max_consecutive_errors = 10
    
    while True:
        try:
            await check_and_complete_raffles()
            consecutive_errors = 0  # Сбрасываем счетчик ошибок при успешной проверке
            # Проверяем каждую минуту
            await asyncio.sleep(60)
        except KeyboardInterrupt:
            logger.info("Планировщик остановлен пользователем")
            break
        except SystemExit:
            logger.info("Планировщик завершен")
            break
        except Exception as e:
            consecutive_errors += 1
            logger.error(f"Ошибка в планировщике (попытка {consecutive_errors}/{max_consecutive_errors}): {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Если слишком много ошибок подряд, делаем более длинную паузу
            if consecutive_errors >= max_consecutive_errors:
                logger.error(f"Слишком много ошибок подряд ({consecutive_errors}). Пауза 5 минут перед следующей попыткой...")
                await asyncio.sleep(300)  # 5 минут
                consecutive_errors = 0  # Сбрасываем счетчик после длинной паузы
            else:
                await asyncio.sleep(60)  # Обычная пауза
