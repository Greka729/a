import aiohttp
from typing import Dict, List, Optional

from .base import BaseParser
from app.utils.http import create_aiohttp_session

SYMBOL_TO_BITGET = {
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

class BitgetParser(BaseParser):
    """Parser for Bitget ticker price (spot)"""

    def __init__(self, api_key: Optional[str] = None):
        self.base_url = "https://api.bitget.com"
        self.api_key = api_key
        self._headers = {"ACCESS-KEY": api_key} if api_key else {}
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = create_aiohttp_session(headers=self._headers, verify=True)
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def get_current_price(self, symbol: str) -> Dict:
        pair = SYMBOL_TO_BITGET.get(symbol.upper())
        if not pair:
            raise ValueError("Unsupported symbol for Bitget")
        session = await self._get_session()
        # Bitget spot ticker endpoint
        url = f"{self.base_url}/api/v2/spot/market/tickers?symbol={pair}"
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            resp.raise_for_status()
            data = await resp.json()
            if data.get("data"):
                last = data["data"][0].get("lastPr") or data["data"][0].get("close")
                return {"symbol": symbol.upper(), "price": float(last), "source": "bitget", "currency": "USDT"}
            raise ValueError("Unexpected Bitget response")

    async def get_historical_data(self, symbol: str, days: int) -> List[Dict]:
        return []
