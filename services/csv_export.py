"""
Модуль для экспорта данных участников в CSV
"""
import csv
import io
from datetime import datetime
from sqlalchemy.orm import Session
from database.db_session import get_db
from database.models import Raffle, Participant, BotUser, Ticket, ReferralLink
from typing import Optional


def generate_csv_for_raffle(raffle_id: int) -> Optional[bytes]:
    """Генерирует CSV файл с данными участников розыгрыша"""
    try:
        db = next(get_db())
        
        # Получаем розыгрыш
        raffle = db.query(Raffle).filter_by(id=raffle_id).first()
        if not raffle:
            return None
        
        # Получаем всех участников
        participants = db.query(Participant).filter_by(raffle_id=raffle_id).all()
        
        # Создаем CSV в памяти
        output = io.StringIO()
        writer = csv.writer(output, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        
        # Заголовки
        writer.writerow([
            'User ID',
            'Username',
            'Имя',
            'Фамилия',
            'Дата участия',
            'Время участия',
            'ID розыгрыша',
            'Название розыгрыша',
            'Реферальный код',
            'Количество приглашенных',
            'Количество билетов',
            'Победитель'
        ])
        
        # Данные участников
        for participant in participants:
            # Получаем количество билетов
            tickets_count = db.query(Ticket).filter_by(user_id=participant.user_id).count()
            
            # Получаем количество приглашенных
            referral_count = db.query(ReferralLink).filter_by(
                creator_id=participant.user_id,
                is_used=True
            ).count()
            
            writer.writerow([
                participant.user_id,
                participant.username or '',
                participant.first_name or '',
                participant.last_name or '',
                participant.joined_at.strftime('%d.%m.%Y') if participant.joined_at else '',
                participant.joined_at.strftime('%H:%M:%S') if participant.joined_at else '',
                raffle.id,
                raffle.name,
                participant.referral_code or '',
                referral_count,
                tickets_count,
                'Да' if participant.is_winner else 'Нет'
            ])
        
        # Конвертируем в bytes
        csv_content = output.getvalue()
        output.close()
        
        return csv_content.encode('utf-8-sig')  # UTF-8 с BOM для Excel
        
    except Exception as e:
        print(f"Ошибка при генерации CSV: {e}")
        return None
    finally:
        db.close()


def get_csv_filename(raffle_id: int, raffle_name: str) -> str:
    """Генерирует имя файла для CSV"""
    # Очищаем название от недопустимых символов
    safe_name = "".join(c for c in raffle_name if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_name = safe_name[:50]  # Ограничиваем длину
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"raffle_{raffle_id}_{safe_name}_{timestamp}.csv"
