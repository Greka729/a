from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
import asyncio

from app.parsers import BinanceParser, BybitParser, BitgetParser, CoinbaseParser
from app.utils.config import SUPPORTED_SYMBOLS as CONF_SYMBOLS
from app.utils.logging import setup_logging
from app.models.db import init_db

app = FastAPI(title="Crypto Analysis API", version="0.1.0")

SUPPORTED_SYMBOLS = [s.upper() for s in CONF_SYMBOLS]
SUPPORTED_SOURCES = ["auto", "binance", "bybit", "bitget", "coinbase"]

class PriceResponse(BaseModel):
    symbol: str
    price: float
    source: str
    currency: Optional[str] = None

class HistoryPoint(BaseModel):
    timestamp: str
    price: float

class IndicatorResponse(BaseModel):
    symbol: str
    indicators: dict

_parsers: dict[str, object] = {}

@app.on_event("startup")
async def on_startup() -> None:
    setup_logging()
    init_db()
    # Initialize parser instances
    _parsers["binance"] = BinanceParser()
    _parsers["bybit"] = BybitParser()
    _parsers["bitget"] = BitgetParser()
    _parsers["coinbase"] = CoinbaseParser()

@app.on_event("shutdown")
async def on_shutdown() -> None:
    # Gracefully close sessions
    tasks = []
    for p in _parsers.values():
        close = getattr(p, "close", None)
        if close:
            tasks.append(close())
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)

@app.get("/", response_class=HTMLResponse)
async def root() -> str:
    return (
        """
        <!doctype html>
        <html>
        <head>
          <meta charset=\"utf-8\" />
          <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
          <title>Crypto Analysis</title>
          <style>body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;margin:32px;} .card{border:1px solid #e5e7eb;border-radius:12px;padding:16px;max-width:540px} .label{color:#6b7280;font-size:12px;text-transform:uppercase;letter-spacing:.06em} .value{font-size:32px;font-weight:700;margin:8px 0} .muted{color:#6b7280} button{padding:8px 12px;border-radius:8px;border:1px solid #e5e7eb;background:#f9fafb;cursor:pointer} button:hover{background:#f3f4f6} select{padding:6px;border-radius:8px;border:1px solid #e5e7eb;margin-left:8px}</style>
        </head>
        <body>
          <div class=\"card\">
            <div class=\"label\">Current Price</div>
            <div id=\"value\" class=\"value\">—</div>
            <div class=\"muted\">Source: <span id=\"source\">—</span></div>
            <div class=\"muted\">Currency: <span id=\"currency\">USD</span></div>
            <div class=\"muted\" id=\"error\" style=\"color:#dc2626;margin-top:6px\"></div>
            <div style=\"margin-top:12px\">
              <button onclick=\"load()\">Reload</button>
              <label>Symbol:
                <select id=\"symbol\">
                  <option>BTC</option><option>ETH</option><option>BNB</option><option>ADA</option><option>XRP</option><option>SOL</option><option>DOT</option><option>DOGE</option><option>AVAX</option><option>MATIC</option>
                </select>
              </label>
              <label>Source:
                <select id=\"sourceSel\">
                  <option>auto</option><option>binance</option><option>bybit</option><option>bitget</option><option>coinbase</option>
                </select>
              </label>
              <a href=\"/docs\" style=\"margin-left:12px\">API Docs</a>
            </div>
          </div>
          <script>
            const coinbaseSupported = new Set(['BTC','ETH','ADA','XRP','SOL','DOT','DOGE','AVAX','MATIC']);
            function enforceSourceCompatibility() {
              const symSel = document.getElementById('symbol');
              const srcSel = document.getElementById('sourceSel');
              const err = document.getElementById('error');
              const sym = symSel.value;
              const isSupported = coinbaseSupported.has(sym);
              // Disable Coinbase option dynamically based on symbol
              for (const opt of srcSel.options) {
                if (opt.value === 'coinbase') {
                  opt.disabled = !isSupported;
                }
              }
              // If currently set to coinbase but unsupported, auto-switch to auto and inform user
              if (srcSel.value === 'coinbase' && !isSupported) {
                srcSel.value = 'auto';
                err.textContent = 'Coinbase не поддерживает выбранный символ. Источник переключен на auto.';
                setTimeout(() => { if (err.textContent.includes('Coinbase')) err.textContent = ''; }, 4000);
              }
            }
            function formatUSD(n) {
              const num = Number(n);
              if (!Number.isFinite(num)) return n;
              return '$ ' + num.toLocaleString(undefined, { maximumFractionDigits: 8 });
            }
            async function load() {
              const sym = document.getElementById('symbol').value;
              const src = document.getElementById('sourceSel').value;
              const err = document.getElementById('error');
              err.textContent = '';
              try {
                const res = await fetch(`/api/crypto/${sym}?source=${src}`);
                if (!res.ok) {
                  const t = await res.text();
                  throw new Error(`HTTP ${res.status}: ${t}`);
                }
                const data = await res.json();
                document.getElementById('value').textContent = formatUSD(data.price);
                document.getElementById('source').textContent = data.source || '—';
                document.getElementById('currency').textContent = 'USD';
              } catch (e) {
                document.getElementById('value').textContent = 'Error';
                document.getElementById('source').textContent = '—';
                document.getElementById('currency').textContent = 'USD';
                err.textContent = e && e.message ? e.message : 'Request failed';
              }
            }
            // Hook up change listeners
            document.getElementById('symbol').addEventListener('change', () => { enforceSourceCompatibility(); load(); });
            document.getElementById('sourceSel').addEventListener('change', () => { enforceSourceCompatibility(); load(); });
            enforceSourceCompatibility();
            load();
          </script>
        </body>
        </html>
        """
    )

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

@app.get("/api/crypto/{symbol}", response_model=PriceResponse)
async def get_current_price(symbol: str, source: str = "auto"):
    symbol = symbol.upper()
    src = source.lower()
    if symbol not in SUPPORTED_SYMBOLS:
        raise HTTPException(status_code=400, detail="Unsupported symbol")
    if src not in SUPPORTED_SOURCES:
        raise HTTPException(status_code=400, detail="Unsupported source")

    async def fetch_from(src_name: str):
        parser = _parsers.get(src_name)
        if not parser:
            raise HTTPException(status_code=503, detail="Parser not ready")
        return await parser.get_current_price(symbol)

    errors: list[str] = []
    sources_order = [src] if src != "auto" else ["binance", "bybit", "bitget", "coinbase"]
    for s in sources_order:
        try:
            data = await fetch_from(s)
            return PriceResponse(**data)
        except Exception as e:  # noqa: BLE001
            # If a specific source was requested (not auto) and it doesn't support the symbol,
            # return a clear 400 instead of aggregating into a 502.
            if src != "auto" and isinstance(e, ValueError):
                raise HTTPException(status_code=400, detail=f"{s}: {e}")
            errors.append(f"{s}: {e}")
            continue
    raise HTTPException(status_code=502, detail="; ".join(errors) or "All sources failed")

@app.get("/api/crypto/{symbol}/history", response_model=List[HistoryPoint])
async def get_history(symbol: str, days: int = 7, source: str = "binance"):
    symbol = symbol.upper()
    src = source.lower()
    if symbol not in SUPPORTED_SYMBOLS:
        raise HTTPException(status_code=400, detail="Unsupported symbol")
    if src not in SUPPORTED_SOURCES:
        raise HTTPException(status_code=400, detail="Unsupported source")
    parser = _parsers.get(src)
    if not parser:
        raise HTTPException(status_code=503, detail="Parser not ready")
    history = await parser.get_historical_data(symbol, days)
    return [HistoryPoint(**p) for p in history]

@app.get("/api/crypto/{symbol}/indicators", response_model=IndicatorResponse)
async def get_indicators(symbol: str, window: int = 14):
    symbol = symbol.upper()
    if symbol not in SUPPORTED_SYMBOLS:
        raise HTTPException(status_code=400, detail="Unsupported symbol")
    return IndicatorResponse(symbol=symbol, indicators={})

@app.get("/api/crypto/correlations")
async def get_correlations(symbols: Optional[List[str]] = None):
    return {"correlations": {}}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
