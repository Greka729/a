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
        timeout = aiohttp.ClientTimeout(total=10)
        def _extract_price(item: Dict) -> Optional[float]:
            candidates = [
                item.get("lastPr"), item.get("close"), item.get("last"), item.get("markPr"), item.get("markPrice"),
                item.get("bidPr"), item.get("askPr"), item.get("bestBid"), item.get("bestAsk"),
                item.get("buyOne"), item.get("sellOne"), item.get("bid1Price"), item.get("ask1Price"),
            ]
            # If we have both bid and ask variants, prefer mid
            bid = None
            ask = None
            for k in ("bidPr", "bestBid", "buyOne", "bid1Price"):
                if item.get(k) is not None:
                    try:
                        bid = float(item.get(k))
                        break
                    except Exception:
                        pass
            for k in ("askPr", "bestAsk", "sellOne", "ask1Price"):
                if item.get(k) is not None:
                    try:
                        ask = float(item.get(k))
                        break
                    except Exception:
                        pass
            for c in candidates:
                if c is not None:
                    try:
                        return float(c)
                    except Exception:
                        continue
            if bid is not None and ask is not None:
                return (bid + ask) / 2.0
            return None

        # Try Bitget v2 single-ticker (singular) with explicit product suffix (symbol format: {PAIR}_SPBL)
        inst = f"{pair}_SPBL"
        url_v2_ticker_single = f"{self.base_url}/api/v2/spot/market/ticker?symbol={inst}"
        async with session.get(url_v2_ticker_single, timeout=timeout) as resp:
            if resp.status == 200:
                data = await resp.json()
                item = (data.get("data") or {})
                if isinstance(item, dict) and item:
                    price_val = _extract_price(item)
                    if price_val is not None:
                        return {"symbol": symbol.upper(), "price": price_val, "source": "bitget", "currency": "USDT"}
        # Try Bitget v2 multi (tickers) with symbol inst id
        url_v2_single_as_list = f"{self.base_url}/api/v2/spot/market/tickers?symbol={inst}"
        async with session.get(url_v2_single_as_list, timeout=timeout) as resp:
            if resp.status == 200:
                data = await resp.json()
                items = data.get("data") or []
                if items:
                    price_val = _extract_price(items[0])
                    if price_val is not None:
                        return {"symbol": symbol.upper(), "price": price_val, "source": "bitget", "currency": "USDT"}
        # Bitget v2 spot ticker endpoint: fetch list by productType to avoid 400 on unknown symbol
        url_v2_list = f"{self.base_url}/api/v2/spot/market/tickers?productType=spbl"
        async with session.get(url_v2_list, timeout=timeout) as resp:
            if resp.status == 200:
                data = await resp.json()
                items = data.get("data") or []
                for it in items:
                    sym_field = (it.get("symbol") or it.get("instId") or "").upper()
                    if sym_field == pair or sym_field == inst:
                        price_val = _extract_price(it)
                        if price_val is not None:
                            return {"symbol": symbol.upper(), "price": price_val, "source": "bitget", "currency": "USDT"}
                    # Some responses include dash or different casing
                    if pair in sym_field or inst in sym_field:
                        price_val = _extract_price(it)
                        if price_val is not None:
                            return {"symbol": symbol.upper(), "price": price_val, "source": "bitget", "currency": "USDT"}
        # Fallback to v1 list endpoint, then filter
        url_v1_list = f"{self.base_url}/api/spot/v1/market/tickers"
        async with session.get(url_v1_list, timeout=timeout) as resp:
            resp.raise_for_status()
            data = await resp.json()
            dat = data.get("data") or []
            # v1 returns list of tickers with 'symbol' and 'last'
            for it in dat:
                sym_field = (it.get("symbol") or it.get("instId") or "").upper()
                if sym_field == pair or sym_field == inst or pair in sym_field or inst in sym_field:
                    price_val = _extract_price(it)
                    if price_val is None:
                        # v1 common fields
                        last = it.get("last") or it.get("close")
                        if last is not None:
                            price_val = float(last)
                    if price_val is not None:
                        return {"symbol": symbol.upper(), "price": price_val, "source": "bitget", "currency": "USDT"}
        # Final attempts: v1 single ticker with inst and with pair
        for sym in (inst, pair):
            url_v1_single = f"{self.base_url}/api/spot/v1/market/ticker?symbol={sym}"
            async with session.get(url_v1_single, timeout=timeout) as resp:
                if resp.status != 200:
                    continue
                data = await resp.json()
                item = data.get("data")
                if isinstance(item, list):
                    item = item[0] if item else {}
                item = item or {}
                price_val = _extract_price(item)
                if price_val is None:
                    last = item.get("last") or item.get("close")
                    if last is not None:
                        price_val = float(last)
                if price_val is not None:
                    return {"symbol": symbol.upper(), "price": price_val, "source": "bitget", "currency": "USDT"}
        raise ValueError("Unexpected Bitget response")

    async def get_historical_data(self, symbol: str, days: int) -> List[Dict]:
        return []
