from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.game.dao import UserDAO
from app.game.schemas import (
    TelegramIDModel,
    SetBestScoreRequest,
    SetBestScoreResponse,
    UserModel,
)
import logging
import traceback


router = APIRouter(prefix='', tags=['ИГРА'])
templates = Jinja2Templates(directory='app/templates')


@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.put("/api/bestScore/{user_id}", response_model=SetBestScoreResponse, summary="Set Best Score")
async def set_best_score(
        user_id: int,
        request: SetBestScoreRequest,
        session: AsyncSession = Depends(get_session)
):
    """
    Установить лучший счет пользователя.
    Обновляет значение `best_score` в базе данных для текущего `user_id`.
    """
    try:
        score = request.score
        user = await UserDAO.find_one_or_none(session=session, filters=TelegramIDModel(telegram_id=user_id))
        if user is None:
            # Создаём пользователя, если зашли в WebApp без /start
            values = UserModel(
                telegram_id=user_id,
                username="",
                first_name="",
                last_name="",
                best_score=score,
            )
            user = await UserDAO.add(session=session, values=values)
        else:
            user.best_score = score
            await session.commit()
        return SetBestScoreResponse(status="success", best_score=score)
    except Exception as e:
        logging.error("Failed to set best score for user_id=%s: %s", user_id, e)
        logging.error(traceback.format_exc())
        raise

@router.get("/records", response_class=HTMLResponse)
async def read_records(request: Request, session: AsyncSession = Depends(get_session)):
    # Получаем топовые рекорды с их позициями
    records = await UserDAO.get_top_scores(session=session)
    # Передаем актуальный список рекордов в шаблон
    return templates.TemplateResponse("pages/records.html", {"request": request, "records": records})