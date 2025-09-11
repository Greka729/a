import aiohttp
from typing import Dict, List, Optional

from .base import BaseParser
from app.utils.http import create_aiohttp_session

SYMBOL_TO_BYBIT = {
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

class BybitParser(BaseParser):
    """Parser for Bybit Market API v5 (linear category for USDT perpetual / spot fallback)"""

    def __init__(self, api_key: Optional[str] = None):
        self.base_url = "https://api.bybit.com"
        self.api_key = api_key
        self._headers = {"X-BAPI-API-KEY": api_key} if api_key else {}
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = create_aiohttp_session(headers=self._headers, verify=True)
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def get_current_price(self, symbol: str) -> Dict:
        pair = SYMBOL_TO_BYBIT.get(symbol.upper())
        if not pair:
            raise ValueError("Unsupported symbol for Bybit")
        session = await self._get_session()
        # Try linear category first (USDT contracts); if fails, try spot
        url_linear = f"{self.base_url}/v5/market/tickers?category=linear&symbol={pair}"
        timeout = aiohttp.ClientTimeout(total=10)
        async with session.get(url_linear, timeout=timeout) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data.get("result", {}).get("list"):
                    last = data["result"]["list"][0].get("lastPrice")
                    if last is not None:
                        return {"symbol": symbol.upper(), "price": float(last), "source": "bybit", "currency": "USDT"}
        # Spot fallback
        url_spot = f"{self.base_url}/v5/market/tickers?category=spot&symbol={pair}"
        async with session.get(url_spot, timeout=timeout) as resp:
            resp.raise_for_status()
            data = await resp.json()
            last = data.get("result", {}).get("list", [{}])[0].get("lastPrice")
            return {"symbol": symbol.upper(), "price": float(last), "source": "bybit", "currency": "USDT"}

    async def get_historical_data(self, symbol: str, days: int) -> List[Dict]:
        return []
