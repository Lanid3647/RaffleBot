# database/models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, BigInteger
from sqlalchemy.sql import func
from .db_session import Base


# ТОЛЬКО БАЗОВЫЕ МОДЕЛИ БЕЗ СВЯЗЕЙ - сначала так!
class BotUser(Base):
    __tablename__ = 'bot_users'

    id = Column(BigInteger, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    version = Column(String(20), default='basic')
    premium_until = Column(DateTime)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())


class Channel_tg(Base):
    __tablename__ = 'channels_tg'

    id = Column(Integer, primary_key=True)
    channel_id = Column(String(255), nullable=False)
    channel_name = Column(String(500))
    channel_username = Column(String(255))
    owner_id = Column(Integer, ForeignKey('bot_users.id'))
    created_at = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)
    status = Column(String, default='active')


class Raffle(Base):
    __tablename__ = 'raffles'

    id = Column(Integer, primary_key=True)
    name = Column(String(500), nullable=True, default='Без названия')
    owner_id = Column(BigInteger, ForeignKey('bot_users.telegram_id'))
    winner_type = Column(String(50), default='auto')
    winners_count = Column(Integer, default=1)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    status = Column(String(50), default='draft')
    media_type = Column(String(100))
    media_file_id = Column(String(500))
    media_caption = Column(Text)
    created_at = Column(DateTime, default=func.now())
    referral_bonus_enable = Column(Boolean, default=False)
    referral_bonus_tickets = Column(Integer, default=0)
    referral_bonus_required = Column(Integer, default=1)
    publication_channels = Column(String(1000), nullable=True)
    subscription_channels = Column(String(1000), nullable=True)
    luck_boost_enabled = Column(Boolean, default=False)
    captcha_enabled = Column(Boolean, default=False)


"""class Participant(Base):
    __tablename__ = 'participants'

    id = Column(Integer, primary_key=True, index=True)
    raffle_id = Column(Integer, ForeignKey('raffles.id'), nullable=False, index=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    tickets_count = Column(Integer, default=1)
    referral_code = Column(String(300))
    referral_count = Column(Integer, default=0)
    is_winner = Column(Boolean, default=False)
    registration_date = Column(DateTime, default=datetime.utcnow)
    joined_at = Column(DateTime, default=datetime.utcnow)

    # Связи
    raffle = relationship("Raffle", back_populates="participants")"""


#  id SERIAL PRIMARY KEY, (уникальный номер)
#     raffle_id (указывет в каком розыгрыше учавствует человек)
#     user_id (тулеграм id )
#
#
#     username
#     first_name
#     last_name
#
#
#     tickets_count (Сколько билетов у участника)
#     referral_code ( Код для приглашения друзей)
#     referral_count (Сколько друзей пригласил)
#     is_winner (Победил ли в розыгрыше)
#
#     registration_date (Когда зарегистрировался в боте)
#     joined_at (Когда присоединился к розыгрышу)
#
#     -- Уникальное ограничение: один человек = одно участие в розыгрыше
#     CONSTRAINT uq_raffle_user UNIQUE (raffle_id, user_id)
# );


# -- Индексы для participants (самая важная таблица после raffles)
# CREATE INDEX idx_participants_raffle_id ON participants(raffle_id); ( Когда нужно найти ВСЕХ участников конкретного розыгрыша.)
# CREATE INDEX idx_participants_user_id ON participants(user_id); (Когда нужно найти ВСЕ розыгрыши, где участвует конкретный пользователь.)
# CREATE INDEX idx_participants_raffle_winner ON participants(raffle_id, is_winner); (# В личном кабинете: "В каких розыгрышах я участвовал?")
# CREATE INDEX idx_participants_joined_at ON participants(joined_at DESC); (СОСТАВНОЙ индекс для быстрого поиска победителей.)
#
# -- Индексы для raffles (очень важны для мини-приложения!)
# CREATE INDEX idx_raffles_status ON raffles(status);
# CREATE INDEX idx_raffles_end_date ON raffles(end_date);
# CREATE INDEX idx_raffles_owner_id ON raffles(owner_id);
#
# -- Индексы для других таблиц
# CREATE INDEX idx_bot_users_telegram_id ON bot_users(telegram_id);
# CREATE INDEX idx_channels_owner ON channels_tg(owner_id);