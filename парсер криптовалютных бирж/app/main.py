from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
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

class ExchangePrice(BaseModel):
    source: str
    price: float
    currency: Optional[str] = None

class DiffSummary(BaseModel):
    symbol: str
    prices: List[ExchangePrice]
    min_price: float
    min_source: str
    max_price: float
    max_source: str
    spread_abs: float
    spread_pct: float
    pairwise: Dict[str, Dict[str, Any]]

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
          <style>
            * { box-sizing: border-box; }
            body {
              font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
              margin: 0;
              padding: 32px;
              min-height: 100vh;
              display: flex;
              justify-content: center;
              align-items: center;
              background: linear-gradient(120deg, #1e3a8a, #7c3aed, #0ea5e9, #22c55e);
              background-size: 300% 300%;
              animation: bgShift 14s ease infinite;
            }
            @keyframes bgShift {
              0% { background-position: 0% 50%; }
              50% { background-position: 100% 50%; }
              100% { background-position: 0% 50%; }
            }
            .container {
              width: 100%;
              max-width: 600px;
              display: flex;
              justify-content: center;
            }
            .card {
              border: 1px solid #e5e7eb;
              border-radius: 16px;
              padding: 24px;
              width: 100%;
              background: rgba(255, 255, 255, 0.95);
              backdrop-filter: blur(10px);
              box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
              transition: transform .2s ease, box-shadow .2s ease;
            }
            .card:hover { transform: translateY(-2px); box-shadow: 0 25px 35px -10px rgba(0,0,0,.15), 0 10px 12px -6px rgba(0,0,0,.08); }
            .label {
              color: #6b7280;
              font-size: 12px;
              text-transform: uppercase;
              letter-spacing: .06em;
              font-weight: 600;
            }
            .value {
              font-size: 40px;
              font-weight: 700;
              margin: 12px 0;
              color: transparent;
              background: linear-gradient(90deg, #111827, #0ea5e9, #22c55e, #111827);
              -webkit-background-clip: text;
              background-clip: text;
              background-size: 200% 100%;
              animation: glow 6s ease-in-out infinite;
            }
            @keyframes glow { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
            .muted {
              color: #6b7280;
              font-size: 14px;
            }
            button {
              padding: 10px 16px;
              border-radius: 8px;
              border: 1px solid #e5e7eb;
              background: #f9fafb;
              cursor: pointer;
              font-weight: 500;
              transition: all 0.2s ease;
            }
            button:hover {
              background: #f3f4f6;
              transform: translateY(-1px);
              box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            }
            button[disabled] { opacity: .6; cursor: not-allowed; transform: none; box-shadow: none; }
            select {
              padding: 8px 12px;
              border-radius: 8px;
              border: 1px solid #e5e7eb;
              margin-left: 8px;
              background: white;
              font-size: 14px;
            }
            .controls {
              display: flex;
              flex-wrap: wrap;
              gap: 12px;
              align-items: center;
              margin-top: 16px;
            }
            .controls label {
              display: flex;
              align-items: center;
              font-size: 14px;
              font-weight: 500;
            }
            .row { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
            .spinner { display: inline-block; width: 14px; height: 14px; border: 2px solid #e5e7eb; border-top-color: #3b82f6; border-radius: 50%; animation: spin 1s linear infinite; vertical-align: -2px; margin-left: 8px; }
            @keyframes spin { to { transform: rotate(360deg); } }
            a {
              color: #3b82f6;
              text-decoration: none;
              font-weight: 500;
            }
            a:hover {
              text-decoration: underline;
            }
            @media (max-width: 640px) {
              body {
                padding: 16px;
              }
              .card {
                padding: 20px;
              }
              .value {
                font-size: 28px;
              }
              .controls {
                flex-direction: column;
                align-items: stretch;
              }
              .controls label {
                justify-content: space-between;
              }
            }
          </style>
        </head>
        <body>
          <div class=\"container\">
            <div class=\"card\">
            <div class=\"row\">\n              <div>\n                <div class=\"label\">Current Price</div>\n                <div id=\"value\" class=\"value\">—</div>\n              </div>\n              <div class=\"muted\" style=\"text-align:right\">\n                <div>Source: <span id=\"source\">—</span></div>\n                <div>Currency: <span id=\"currency\">USD</span></div>\n              </div>\n            </div>
            <div class=\"muted\" id=\"error\" style=\"color:#dc2626;margin-top:6px\"></div>
            <div class=\"label\" style=\"margin-top:16px\">Spreads across exchanges</div>
            <div id=\"spreads\" class=\"muted\">—</div>
            <div style=\"margin-top:8px\">
              <canvas id=\"spreadChart\" width=\"520\" height=\"220\" style=\"width:100%;max-width:520px;height:220px;border:1px solid #e5e7eb;border-radius:8px;background:#fff\"></canvas>
            </div>
            <div class=\"controls\">
              <button id="reloadBtn" onclick="load()">Reload</button>
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
              <label>Auto refresh:
                <select id="intervalSel">
                  <option value="0">Off</option>
                  <option value="5000">5s</option>
                  <option value="10000">10s</option>
                  <option value="30000">30s</option>
                </select>
              </label>
              <span id="loading" style="display:none"><span class="spinner"></span></span>
              <a href="/docs">API Docs</a>
            </div>
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
                } else if (opt.value === 'bybit' || opt.value === 'bitget') {
                  opt.disabled = (sym === 'MATIC');
                } else {
                  opt.disabled = false;
                }
              }
              const currentOption = Array.from(srcSel.options).find(o => o.value === srcSel.value);
              if (currentOption && currentOption.disabled) {
                srcSel.value = 'auto';
                if (!isSupported && currentOption.value === 'coinbase') {
                  err.textContent = 'Coinbase не поддерживает выбранный символ. Источник переключен на auto.';
                } else if (sym === 'MATIC' && (currentOption.value === 'bybit' || currentOption.value === 'bitget')) {
                  err.textContent = 'Bybit и Bitget отключены для MATIC. Источник переключен на auto.';
                }
                setTimeout(() => { err.textContent = ''; }, 4000);
              }
            }
            function formatUSD(n) {
               const num = Number(n);
               if (!Number.isFinite(num)) return n;
               return '$ ' + num.toLocaleString(undefined, { maximumFractionDigits: 8 });
             }
            function setLoading(isLoading) {
              const btn = document.getElementById('reloadBtn');
              const spinner = document.getElementById('loading');
              if (btn) btn.disabled = !!isLoading;
              if (spinner) spinner.style.display = isLoading ? 'inline-block' : 'none';
            }
            let lastPrices = [];
            function resizeCanvasForDPR(canvas) {
              const dpr = Math.max(1, window.devicePixelRatio || 1);
              const rect = canvas.getBoundingClientRect();
              const cssWidth = Math.max(320, rect.width || 520);
              const cssHeight = Math.max(160, rect.height || 220);
              canvas.width = Math.round(cssWidth * dpr);
              canvas.height = Math.round(cssHeight * dpr);
              const ctx = canvas.getContext('2d');
              ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
              return { ctx, width: cssWidth, height: cssHeight };
            }
            async function load() {
              const sym = document.getElementById('symbol').value;
              const src = document.getElementById('sourceSel').value;
              const err = document.getElementById('error');
              err.textContent = '';
              setLoading(true);
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
                // Load spreads in parallel (best-effort)
                loadSpreads(sym);
              } catch (e) {
                document.getElementById('value').textContent = 'Error';
                document.getElementById('source').textContent = '—';
                document.getElementById('currency').textContent = 'USD';
                err.textContent = e && e.message ? e.message : 'Request failed';
              } finally { setLoading(false); }
            }
            async function loadSpreads(sym) {
              const el = document.getElementById('spreads');
              el.textContent = 'Loading…';
              try {
                const res = await fetch(`/api/crypto/${sym}/diffs`);
                if (!res.ok) {
                  el.textContent = '—';
                  drawSpreadChart([]);
                  return;
                }
                const d = await res.json();
                const parts = [];
                parts.push(`Min: ${d.min_source} ${formatUSD(d.min_price)}`);
                parts.push(`Max: ${d.max_source} ${formatUSD(d.max_price)}`);
                parts.push(`Spread: ${formatUSD(d.spread_abs)} (${d.spread_pct.toFixed(3)}%)`);
                el.textContent = parts.join('  |  ');
                lastPrices = d.prices || [];
                drawSpreadChart(lastPrices);
              } catch (_e) {
                el.textContent = '—';
                drawSpreadChart([]);
              }
            }
            function drawSpreadChart(prices) {
              const canvas = document.getElementById('spreadChart');
              if (!canvas) return;
              const { ctx, width, height } = resizeCanvasForDPR(canvas);
              // Clear
              ctx.clearRect(0, 0, width, height);
              // If no data
              if (!Array.isArray(prices) || prices.length === 0) {
                ctx.fillStyle = '#9ca3af';
                ctx.font = '12px system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif';
                ctx.fillText('Нет данных для графика', 16, 24);
                return;
              }
              const padding = { top: 16, right: 16, bottom: 36, left: 48 };
              const innerW = width - padding.left - padding.right;
              const innerH = height - padding.top - padding.bottom;
              // Compute min/max
              const values = prices.map(p => Number(p.price)).filter(n => Number.isFinite(n));
              const minV = Math.min(...values);
              const maxV = Math.max(...values);
              const span = Math.max(1e-9, maxV - minV);
              // Axes
              ctx.strokeStyle = '#e5e7eb';
              ctx.lineWidth = 1;
              // y-axis
              ctx.beginPath();
              ctx.moveTo(padding.left, padding.top);
              ctx.lineTo(padding.left, padding.top + innerH);
              ctx.stroke();
              // x-axis
              ctx.beginPath();
              ctx.moveTo(padding.left, padding.top + innerH);
              ctx.lineTo(padding.left + innerW, padding.top + innerH);
              ctx.stroke();
              // Y ticks (4)
              ctx.fillStyle = '#6b7280';
              ctx.font = '11px system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif';
              const ticks = 4;
              for (let i = 0; i <= ticks; i++) {
                const t = i / ticks;
                const y = padding.top + innerH - t * innerH;
                ctx.strokeStyle = '#f3f4f6';
                ctx.beginPath();
                ctx.moveTo(padding.left, y);
                ctx.lineTo(padding.left + innerW, y);
                ctx.stroke();
                const val = minV + t * span;
                ctx.fillStyle = '#6b7280';
                ctx.fillText(formatUSD(val), 6, y - 2);
              }
              // Bars
              const n = prices.length;
              const barGap = Math.min(18, innerW / Math.max(1, n) * 0.25);
              const barW = Math.max(8, (innerW / n) - barGap);
              const baseY = padding.top + innerH;
              const colors = ['#60a5fa','#34d399','#f472b6','#fbbf24','#a78bfa','#4ade80','#f97316','#22d3ee'];
              prices.forEach((p, idx) => {
                const val = Number(p.price);
                const t = (val - minV) / span;
                const h = t * innerH;
                const x = padding.left + idx * (barW + barGap) + barGap * 0.5;
                const y = baseY - h;
                ctx.fillStyle = colors[idx % colors.length];
                ctx.fillRect(x, y, barW, h);
                // label
                ctx.fillStyle = '#111827';
                ctx.font = '11px system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif';
                const label = (p.source || '').toUpperCase();
                const textW = ctx.measureText(label).width;
                const tx = x + (barW - textW) / 2;
                ctx.fillText(label, tx, baseY + 14);
                // value on top
                ctx.fillStyle = '#374151';
                const valText = formatUSD(val);
                const vtW = ctx.measureText(valText).width;
                const vtx = x + (barW - vtW) / 2;
                ctx.fillText(valText, vtx, y - 4);
              });
            }
            function applyInterval() {
              const sel = document.getElementById('intervalSel');
              const ms = Number(sel && sel.value ? sel.value : 0) || 0;
              if (window.__priceTimer) { clearInterval(window.__priceTimer); window.__priceTimer = null; }
              if (ms > 0) {
                window.__priceTimer = setInterval(() => { load(); }, ms);
              }
            }
            // Hook up change listeners
            document.getElementById('symbol').addEventListener('change', () => { enforceSourceCompatibility(); load(); });
            document.getElementById('sourceSel').addEventListener('change', () => { enforceSourceCompatibility(); load(); });
            const intervalSel = document.getElementById('intervalSel');
            if (intervalSel) { intervalSel.addEventListener('change', applyInterval); }
            window.addEventListener('resize', () => { if (lastPrices) drawSpreadChart(lastPrices); });
            enforceSourceCompatibility();
            load();
            applyInterval();
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

@app.get("/api/crypto/{symbol}/diffs", response_model=DiffSummary)
async def get_exchange_differences(symbol: str):
    symbol = symbol.upper()
    if symbol not in SUPPORTED_SYMBOLS:
        raise HTTPException(status_code=400, detail="Unsupported symbol")

    async def fetch_from(src_name: str):
        parser = _parsers.get(src_name)
        if not parser:
            raise HTTPException(status_code=503, detail="Parser not ready")
        return await parser.get_current_price(symbol)

    sources_order = [s for s in ["binance", "bybit", "bitget", "coinbase"] if s in _parsers]
    results = await asyncio.gather(*[fetch_from(s) for s in sources_order], return_exceptions=True)

    prices: List[ExchangePrice] = []
    for src, res in zip(sources_order, results):
        if isinstance(res, Exception):
            # skip failed source
            continue
        try:
            # Normalize to float and treat USD ~= USDT for spread purposes
            price = float(res.get("price"))
            curr = res.get("currency")
            prices.append(ExchangePrice(source=src, price=price, currency=curr))
        except Exception:  # noqa: BLE001
            continue

    if len(prices) < 2:
        raise HTTPException(status_code=502, detail="Not enough exchange data to compute differences")

    min_entry = min(prices, key=lambda p: p.price)
    max_entry = max(prices, key=lambda p: p.price)
    spread_abs = max_entry.price - min_entry.price
    spread_pct = (spread_abs / min_entry.price * 100.0) if min_entry.price else 0.0

    # Pairwise matrix: key "srcA-srcB"
    pairwise: Dict[str, Dict[str, Any]] = {}
    for i in range(len(prices)):
        for j in range(i + 1, len(prices)):
            a = prices[i]
            b = prices[j]
            key = f"{a.source}-{b.source}"
            diff_abs = abs(a.price - b.price)
            base = min(a.price, b.price)
            diff_pct = (diff_abs / base * 100.0) if base else 0.0
            pairwise[key] = {
                "a": {"source": a.source, "price": a.price},
                "b": {"source": b.source, "price": b.price},
                "diff_abs": diff_abs,
                "diff_pct": diff_pct,
            }

    return DiffSummary(
        symbol=symbol,
        prices=prices,
        min_price=min_entry.price,
        min_source=min_entry.source,
        max_price=max_entry.price,
        max_source=max_entry.source,
        spread_abs=spread_abs,
        spread_pct=spread_pct,
        pairwise=pairwise,
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
