from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import os
import json
import logging
from typing import Optional
import math

from database.db_session import DATABASE_URL, SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app == FastAPI(title="Telegram MiniApp API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    alow_methods=["*"],
    alow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

DATABASE_URL = "postgresql://bot_user:9349386375365@localhost:5432/raffle_bot"

try:
    engine = create_engine(DATABASE_URL)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # тестируем подключение
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    logger.info("✅ PostgreSQL подключена успешно!")

except Exception as e:
    logger.error(f"❌ Ошибка подключения к PostgreSQL: {e}")
    engine = None
    SessionLocal = None


# получение сессии базы данных
def get_db():
    if SessionLocal is None:
        raise Exception("База данных не подключена")
    db = SessionLocal()
    try:
        return  db
    finally:
        db.close()

# получение данных розыгрыша из базы данных

def get_raffle_from_db(raffle_id: int):
    if engine is None:
        logger.error("PostgreSQL не подключена")
        return None

    db = get_db()
    try:
        query = text("""
            SELECT 
                    id, name, winner_type, winners_count, 
                    start_date, end_date, status,
                    media_type, media_file_id, media_caption,
                    subscription_channels, publication_channels,
                    luck_boost_enabled, captcha_enabled
                FROM raffles 
                WHERE id = :raffle_id
        """)
        result = db.execute(query, {"raffle_id": raffle_id})
        raffle = result.fetchone()

        if not raffle:
            return None

        raffle_dict = {
            "id": raffle[0],
            "name": raffle[1] or "Розыгрыш",
            "winner_type": raffle[2] or "auto",
            "winners_count": raffle[3] or 1,
            "start_date": raffle[4],
            "end_date": raffle[5],
            "status": raffle[6] or "active",
            "media_type": raffle[7],
            "media_file_id": raffle[8],
            "media_caption": raffle[9] or "",
            "subscription_channels": raffle[10],
            "publication_channels": raffle[11],
            "luck_boost_enabled": raffle[12] or False,
            "captcha_enabled": raffle[13] or False
        }

        logger.info(f"✅ Получен розыгрыш #{raffle_id}: {raffle_dict['name']}")
        return raffle_dict

    except Exception as e:
        logger.error(f"❌ Ошибка получения розыгрыша #{raffle_id}: {e}")
        return None
    finally:
        db.close()

# получаем каналы для подписок из базы данных
def get_channels_for_subscription(raffle_id: int):
    """Получаем каналы для подписки из БД"""
    if engine is None:
        return []

    db = get_db()
    try:
        # Сначала получаем список каналов из розыгрыша
        query = text("""
            SELECT subscription_channels 
            FROM raffles 
            WHERE id = :raffle_id
        """)

        result = db.execute(query, {"raffle_id": raffle_id})
        row = result.fetchone()

        if not row or not row[0]:
            return []

        # Парсим JSON строку с каналами
        channels_json = row[0]
        if channels_json:
            try:
                channels = json.loads(channels_json)
                if isinstance(channels, list):
                    return channels
            except:
                pass

        return []

    except Exception as e:
        logger.error(f"❌ Ошибка получения каналов: {e}")
        return []
    finally:
        db.close()


def calculate_time_left(end_date):
    """Рассчитывает оставшееся время до окончания розыгрыша"""
    if not end_date:
        return {"hours": 0, "minutes": 0, "seconds": 0, "total_seconds": 0}

    now = datetime.now()
    if isinstance(end_date, str):
        try:
            end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except:
            return {"hours": 0, "minutes": 0, "seconds": 0, "total_seconds": 0}

    if end_date <= now:
        return {"hours": 0, "minutes": 0, "seconds": 0, "total_seconds": 0}

    time_left = end_date - now
    total_seconds = int(time_left.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    return {
        "hours": hours,
        "minutes": minutes,
        "seconds": seconds,
        "total_seconds": total_seconds,
        "formatted": f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    }


def format_date(date_value):
    """Форматируем дату для отображения"""
    if not date_value:
        return "Не указано"

    if isinstance(date_value, str):
        try:
            date_value = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
        except:
            return "Не указано"

    return date_value.strftime("%d.%m.%Y %H:%M")


# Главная страница - мини-приложение
@app.get("/", response_class=HTMLResponse)
async def mini_app(request: Request, raffle_id: Optional[int] = None):
    """Главная страница мини-приложения"""

    # Если raffle_id не указан, используем тестовый
    if not raffle_id:
        raffle_id = 1

    # Получаем данные о розыгрыше из БД
    raffle_data = get_raffle_from_db(raffle_id)

    if not raffle_data:
        # Если розыгрыш не найден
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head><title>Ошибка</title></head>
        <body static
        <static="background: black; color: white; padding: 20px;">
            <h1>❌ Розыгрыш не найден</h1>
            <p>ID: {}</p>
            <p>Проверьте ссылку или обратитесь к администратору.</p>
        </body>
        </html>
        """.format(raffle_id))

    # Рассчитываем оставшееся время
    time_data = calculate_time_left(raffle_data.get('end_date'))

    # Получаем каналы для подписки
    channels = get_channels_for_subscription(raffle_id)

    # Форматируем дату окончания
    end_date_formatted = format_date(raffle_data.get('end_date'))

    # Создаем контекст для шаблона
    context = {
        "request": request,
        "raffle_id": raffle_id,
        "raffle_name": raffle_data.get('name', 'Розыгрыш'),
        "description": raffle_data.get('media_caption', 'Подпишитесь на все указанные ниже каналы'),
        "winners_count": raffle_data.get('winners_count', 1),
        "end_date_formatted": end_date_formatted,
        "time_left_formatted": time_data.get('formatted', '00:00:00'),
        "total_seconds": time_data.get('total_seconds', 0),
        "channels": channels,
        "channels_count": len(channels),
        "status": raffle_data.get('status', 'active')
    }

    # Рендерим HTML шаблон
    return templates.TemplateResponse("check.html", context)


# API для проверки подписки пользователя
@app.post("/api/check-subscription")
async def check_subscription(request: Request):
    """Проверяет подписку пользователя на каналы"""
    try:
        data = await request.json()
        raffle_id = data.get('raffle_id')
        user_id = data.get('user_id')

        if not raffle_id or not user_id:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Недостаточно данных"}
            )

        # Получаем каналы для этого розыгрыша
        channels = get_channels_for_subscription(raffle_id)

        # Здесь будет реальная проверка подписки через Telegram API
        # Пока возвращаем тестовые данные

        subscription_results = []
        all_subscribed = True

        for channel in channels:
            # Тестовые данные - предполагаем что пользователь подписан
            is_subscribed = True  # Замените на реальную проверку

            subscription_results.append({
                "channel": channel,
                "subscribed": is_subscribed,
                "title": f"Канал {channel}"
            })

            if not is_subscribed:
                all_subscribed = False

        return {
            "success": True,
            "all_subscribed": all_subscribed,
            "channels": subscription_results,
            "message": "Проверка завершена" if all_subscribed else "Требуется подписка на каналы"
        }

    except Exception as e:
        logger.error(f"Ошибка проверки подписки: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Ошибка сервера: {str(e)}"}
        )


# API для регистрации участия
@app.post("/api/participate")
async def participate(request: Request):
    """Регистрация участия в розыгрыше"""
    try:
        data = await request.json()
        raffle_id = data.get('raffle_id')
        user_data = data.get('user_data', {})

        if not raffle_id:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "ID розыгрыша не указан"}
            )

        user_id = user_data.get('id')
        if not user_id:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "ID пользователя не получен"}
            )

        # Проверяем подписку
        channels = get_channels_for_subscription(raffle_id)
        if channels:
            # Здесь должна быть реальная проверка подписки
            # Пока предполагаем что подписан
            all_subscribed = True

            if not all_subscribed:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "message": "Требуется подписка на все каналы",
                        "requires_subscription": True,
                        "channels": channels
                    }
                )

        # Проверяем, не участвует ли уже пользователь
        if engine is not None:
            db = get_db()
            try:
                # Ищем участника
                query = text("""
                    SELECT id FROM participants 
                    WHERE raffle_id = :raffle_id AND user_id = :user_id
                """)
                result = db.execute(query, {
                    "raffle_id": raffle_id,
                    "user_id": user_id
                })

                if result.fetchone():
                    # Уже участвует
                    return JSONResponse(
                        status_code=400,
                        content={
                            "success": False,
                            "message": "Вы уже участвуете в этом розыгрыше",
                            "already_participating": True
                        }
                    )

                # Подсчитываем количество билетов пользователя
                tickets_query = text("""
                    SELECT COUNT(*) FROM tickets WHERE user_id = :user_id
                """)
                tickets_result = db.execute(tickets_query, {"user_id": user_id})
                tickets_count = tickets_result.scalar() or 1  # Минимум 1 билет
                
                # Добавляем участника с учетом билетов
                insert_query = text("""
                    INSERT INTO participants 
                    (raffle_id, user_id, username, first_name, last_name, tickets_count, joined_at)
                    VALUES (:raffle_id, :user_id, :username, :first_name, :last_name, :tickets_count, NOW())
                """)

                db.execute(insert_query, {
                    "raffle_id": raffle_id,
                    "user_id": user_id,
                    "username": user_data.get('username'),
                    "first_name": user_data.get('first_name'),
                    "last_name": user_data.get('last_name'),
                    "tickets_count": tickets_count
                })

                db.commit()

                # Считаем количество участников
                count_query = text("""
                    SELECT COUNT(*) FROM participants WHERE raffle_id = :raffle_id
                """)
                count_result = db.execute(count_query, {"raffle_id": raffle_id})
                participants_count = count_result.scalar()

                logger.info(f"✅ Пользователь {user_id} зарегистрирован в розыгрыше #{raffle_id}")

                return {
                    "success": True,
                    "message": "🎉 Вы успешно зарегистрированы в розыгрыше!",
                    "raffle_id": raffle_id,
                    "user_id": user_id,
                    "participant_number": participants_count,
                    "timestamp": datetime.now().isoformat()
                }

            except Exception as e:
                db.rollback()
                logger.error(f"❌ Ошибка записи в БД: {e}")
                return JSONResponse(
                    status_code=500,
                    content={"success": False, "message": f"Ошибка базы данных: {str(e)}"}
                )
            finally:
                db.close()
        else:
            # Если БД недоступна
            return {
                "success": True,
                "message": "✅ Регистрация принята (тестовый режим)",
                "raffle_id": raffle_id,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"❌ Ошибка регистрации: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Ошибка сервера: {str(e)}"}
        )


# API для получения информации о розыгрыше
@app.get("/api/raffle/{raffle_id}")
async def get_raffle_api(raffle_id: int):
    """API для получения данных о розыгрыше"""
    raffle_data = get_raffle_from_db(raffle_id)

    if not raffle_data:
        raise HTTPException(status_code=404, detail="Розыгрыш не найден")

    # Рассчитываем оставшееся время
    time_data = calculate_time_left(raffle_data.get('end_date'))

    # Получаем каналы для подписки
    channels = get_channels_for_subscription(raffle_id)

    return {
        "success": True,
        "raffle": {
            **raffle_data,
            "time_left": time_data,
            "channels": channels,
            "channels_count": len(channels)
        }
    }


# Тестовый endpoint
@app.get("/api/test")
async def test_api():
    """Тестовый endpoint"""
    db_status = "✅ Подключена" if engine else "❌ Не подключена"

    # Пробуем сделать тестовый запрос
    test_result = "Ошибка"
    if engine:
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM raffles"))
                count = result.scalar()
                test_result = f"✅ OK (розыгрышей: {count})"
        except Exception as e:
            test_result = f"❌ Ошибка: {str(e)}"

    return {
        "status": "ok",
        "service": "Telegram MiniApp API",
        "database": db_status,
        "database_test": test_result,
        "timestamp": datetime.now().isoformat()
    }


# Health check
@app.get("/health")
async def health_check():
    """Проверка здоровья сервера"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "connected" if engine else "disconnected"
    }


# Страница для отладки
@app.get("/debug/{raffle_id}")
async def debug_page(raffle_id: int):
    """Страница для отладки данных"""
    raffle_data = get_raffle_from_db(raffle_id)
    channels = get_channels_for_subscription(raffle_id)
    time_data = calculate_time_left(raffle_data.get('end_date') if raffle_data else None)

    return {
        "raffle_id": raffle_id,
        "raffle_data": raffle_data,
        "channels": channels,
        "time_data": time_data,
        "current_time": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)











