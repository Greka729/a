# Crypto Analysis

Минимальный, но удобный API/веб‑интерфейс для получения котировок топ‑монет с разных бирж (Binance, Bybit, Bitget, Coinbase), сравнения цен и быстрого просмотра спредов.

## Возможности
- Темная/светлая тема (переключатель в UI)
- Авто‑обновление цены (5–60 сек)
- Сравнение цен между биржами и визуальный бар‑чарт спредов
- Быстрый статус сервиса на `/api/status`
- Документация Swagger на `/docs`

## Быстрый старт

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows PowerShell: .venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

После запуска:
- UI: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health
- Status: http://localhost:8000/api/status

## Переменные окружения (.env)
Создайте файл `.env` в корне:

```
DATABASE_URL=sqlite:///./crypto.db
SUPPORTED_SYMBOLS=BTC,ETH,BNB,ADA,XRP,SOL,DOT,DOGE,AVAX,MATIC
BINANCE_API_KEY=
```

## Основные эндпоинты
- GET `/api/crypto/{symbol}?source=auto|binance|bybit|bitget|coinbase` — текущая цена
- GET `/api/crypto/{symbol}/diffs` — сводка цен по биржам и спред
- GET `/api/crypto/{symbol}/history?days=7&source=binance` — история (заготовка)
- GET `/api/crypto/{symbol}/indicators?window=14` — индикаторы (заготовка)

Поддерживаемые символы задаются через `SUPPORTED_SYMBOLS`.

## Примечания
- Coinbase не поддерживает некоторые тикеры (например, `BNB`). В UI такие источники автоматически отключаются для неподдерживаемых символов.
- Для `MATIC` источники `bybit` и `bitget` в UI отключены как пример selective‑routing.
