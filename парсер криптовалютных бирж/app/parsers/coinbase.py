import aiohttp
from typing import Dict, List, Optional

from .base import BaseParser
from app.utils.http import create_aiohttp_session

SYMBOL_TO_COINBASE = {
    "BTC": "BTC-USD",
    "ETH": "ETH-USD",
    "BNB": None,  # Coinbase does not list BNB; mark unsupported
    "ADA": "ADA-USD",
    "XRP": "XRP-USD",
    "SOL": "SOL-USD",
    "DOT": "DOT-USD",
    "DOGE": "DOGE-USD",
    "AVAX": "AVAX-USD",
    "MATIC": "MATIC-USD",
}

class CoinbaseParser(BaseParser):
    """Parser for Coinbase Advanced Trade/Public price"""

    def __init__(self, api_key: Optional[str] = None):
        self.base_url = "https://api.coinbase.com"
        self.api_key = api_key
        self._headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = create_aiohttp_session(headers=self._headers, verify=True)
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def get_current_price(self, symbol: str) -> Dict:
        product = SYMBOL_TO_COINBASE.get(symbol.upper())
        if not product:
            raise ValueError("Unsupported symbol for Coinbase")
        session = await self._get_session()
        # Coinbase spot price endpoint
        url = f"{self.base_url}/v2/prices/{product}/spot"
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            resp.raise_for_status()
            data = await resp.json()
            amount = data.get("data", {}).get("amount")
            if amount is None:
                raise ValueError("Unexpected Coinbase response")
            return {"symbol": symbol.upper(), "price": float(amount), "source": "coinbase", "currency": "USD"}

    async def get_historical_data(self, symbol: str, days: int) -> List[Dict]:
        return []
