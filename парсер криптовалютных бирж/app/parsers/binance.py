import aiohttp
from typing import Dict, List, Optional

from .base import BaseParser
from app.utils.http import create_aiohttp_session

SYMBOL_TO_BINANCE = {
    "BTC": "BTCUSDT",
    "ETH": "ETHUSDT",
    "BNB": "BNBUSDT",
    "ADA": "ADAUSDT",
    "XRP": "XRPUSDT",
    "SOL": "SOLUSDT",
    "DOT": "DOTUSDT",
    "DOGE": "DOGEUSDT",
    "AVAX": "AVAXUSDT",
    "MATIC": "MATICUSDT",
}

class BinanceParser(BaseParser):
    """Парсер для Binance API"""

    def __init__(self, api_key: Optional[str] = None):
        self.base_url = "https://api.binance.com"
        self.api_key = api_key
        self._headers = {"X-MBX-APIKEY": api_key} if api_key else {}
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = create_aiohttp_session(headers=self._headers, verify=True)
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def get_current_price(self, symbol: str) -> Dict:
        pair = SYMBOL_TO_BINANCE.get(symbol.upper())
        if not pair:
            raise ValueError("Unsupported symbol for Binance")
        session = await self._get_session()
        url = f"{self.base_url}/api/v3/ticker/price?symbol={pair}"
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return {"symbol": symbol.upper(), "price": float(data["price"]), "source": "binance", "currency": "USDT"}

    async def get_historical_data(self, symbol: str, days: int) -> List[Dict]:
        # Placeholder: use klines endpoint in future
        return []


