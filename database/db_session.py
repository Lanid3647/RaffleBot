# database/db_session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

# URL БЕЗ SSL для теста
# Ранее было: DATABASE_URL = "postgresql://postgres:Fynza3-gocnyw-xurzed@db.osvztgewhvuswokqxlyu.supabase.co:5432/postgres?sslmode=disable"
DATABASE_URL = "postgresql://bot_user:9349386375365@localhost:5432/raffle_bot"

# ИЛИ с минимальным таймаутом
DATABASE_URL_SSL = "postgresql://postgres:Fynza3-gocnyw-xurzed@db.osvztgewhvuswokqxlyu.supabase.co:5432/postgres?sslmode=require"

# Пробуем без SSL сначала
engine = create_engine(
    DATABASE_URL,  # ← БЕЗ SSL
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    echo=False  # Отключаем echo для производительности
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()









