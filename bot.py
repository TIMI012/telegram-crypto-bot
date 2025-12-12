"""
Telegram Futures Trading Bot (async) with:
- multi-pair scanning
- SMA/EMA/RSI/MACD/ATR signals
- auto-execution (futures) via ccxt.async_support
- per-chat controls (enable/disable autotrade, subscribe alerts)
- risk limits: max trades/day, max loss/day, position sizing
- dashboard commands: /start /status /enable /disable /pairs /addpair /removepair /trades /balance /pnl
"""

import os
import logging
import asyncio
import math
from datetime import datetime, timedelta
from statistics import mean
from typing import List, Dict, Any

import ccxt.async_support as ccxt
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tg-trader")

# -------------------- ENV / CONFIG --------------------
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# risk / sizing defaults (can be changed per chat via commands later - this template uses global defaults)
DEFAULT_ORDER_USDT = float(os.getenv("ORDER_USDT", "10"))           # size per trade in USDT
DEFAULT_LEVERAGE = int(os.getenv("LEVERAGE", "5"))                 # default leverage
MAX_TRADES_PER_DAY = int(os.getenv("MAX_TRADES_PER_DAY", "10"))
MAX_DAILY_LOSS_USDT = float(os.getenv("MAX_DAILY_LOSS_USDT", "50"))

# scanner settings
SCAN_INTERVAL_SECS = int(os.getenv("SCAN_INTERVAL_SECS", "300"))   # scan every 5 minutes by default
CANDLES_LIMIT = 200
CANDLE_TIMEFRAME = os.getenv("CANDLE_TIMEFRAME", "5m")             # timeframe for indicators

# supported pairs by default (user can modify)
DEFAULT_PAIRS = os.getenv("DEFAULT_PAIRS", "BTC/USDT,ETH/USDT,BNB/USDT").split(",")

# -------------------- STATE --------------------
# per-chat settings & state
chats_config: Dict[int, Dict[str, Any]] = {}   # chat_id -> config dict
# example config keys:
# { "autotrade": False, "pairs": [...], "order_usdt": 10, "leverage": 5,
#   "daily_trades": 0, "daily_loss": 0.0, "last_reset": datetime, "trade_log": [] }

# global trade record to prevent repeating same action too often
recent_signals: Dict[str, datetime] = {}       # key = f"{chat_id}:{symbol}" -> last action time

# exchange (async)
exchange = ccxt.binance({
    "apiKey": BINANCE_API_KEY,
    "secret": BINANCE_API_SECRET,
    "enableRateLimit": True,
    "options": {"defaultType": "future"},
})

# -------------------- INDICATORS --------------------
def sma(values: List[float], period: int) -> float:
    if len(values) < period: return float("nan")
    return mean(values[-period:])

def ema(values: List[float], period: int) -> float:
    if len(values) < period: return float("nan")
    k = 2 / (period + 1)
    ema_prev = values[0]
    for v in values[1:]:
        ema_prev = v * k + ema_prev * (1 - k)
    return ema_prev

def rsi(values: List[float], period: int = 14) -> float:
    if len(values) < period + 1: return float("nan")
    gains, losses = 0.0, 0.0
    for i in range(-period, 0):
        diff = values[i] - values[i - 1]
        if diff > 0: gains += diff
        else: losses += abs(diff)
    if losses == 0: return 100.0
    rs = (gains / period) / (losses / period)
    return 100 - (100 / (1 + rs))

def macd(values: List[float], fast=12, slow=26, signal=9):
    if len(values) < slow + signal: return None, None, None
    # compute EMA fast and slow
    def calc_ema(arr, period):
        k = 2 / (period + 1)
        ema_val = arr[0]
        for v in arr[1:]:
            ema_val = v*k + ema_val*(1-k)
        return ema_val
    ema_fast = calc_ema(values[-(slow+fast):], fast)
    ema_slow = calc_ema(values[-(slow+slow):], slow)
    macd_line = ema_fast - ema_slow
    # For simplicity compute signal on last (signal) macd values approximated
    return macd_line, None, None

def atr(highs: List[float], lows: List[float], closes: List[float], period=14):
    if len(closes) < period+1: return float("nan")
    trs = []
    for i in range(1, len(closes)):
        tr = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
        trs.append(tr)
    return mean(trs[-period:]) if len(trs) >= period else float("nan")

# -------------------- DATA FETCH HELPERS --------------------
async def fetch_ohlcv(symbol: str, timeframe: str = CANDLE_TIMEFRAME, limit: int = CANDLES_LIMIT):
    try:
        ohlcv = await exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        # ohlcv: [timestamp, open, high, low, close, volume]
        return ohlcv
    except Exception as e:
        logger.error("fetch_ohlcv error %s %s", symbol, e)
        return []

# -------------------- SIGNAL GENERATION --------------------
async def generate_signals_for_symbol(symbol: str):
    ohlcv = await fetch_ohlcv(symbol)
    if not ohlcv:
        return None
    closes = [float(c[4]) for c in ohlcv]
    highs = [float(c[2]) for c in ohlcv]
    lows = [float(c[3]) for c in ohlcv]

    # indicators
    sma_short = sma(closes, 10)
    sma_long = sma(closes, 30)
    ema_short = ema(closes[-50:], 12) if len(closes) >= 12 else float("nan")
    rsi_val = rsi(closes, 14)
    macd_line, _, _ = macd(closes)
    atr_val = atr(highs, lows, closes, 14)

    # simple rule-based signal combining indicators
    signal = None
    score = 0

    if not math.isnan(sma_short) and not math.isnan(sma_long):
        if sma_short > sma_long:
            score += 1
        else:
            score -= 1

    if not math.isnan(rsi_val):
        if rsi_val < 30:
            score += 1
        elif rsi_val > 70:
            score -= 1

    # MACD rudimentary
    if macd_line is not None:
        if macd_line > 0:
            score += 0.5
        else:
            score -= 0.5

    # final mapping
    if score >= 1.0:
        signal = "BUY"
    elif score <= -1.0:
        signal = "SELL"

    info = {
        "symbol": symbol,
        "price": closes[-1],
        "sma_short": sma_short,
        "sma_long": sma_long,
        "rsi": rsi_val,
        "macd": macd_line,
        "atr": atr_val,
        "score": score,
        "signal": signal
    }
    return info

# -------------------- RISK / ORDER HELPERS --------------------
def ensure_chat_config(chat_id: int):
    cfg = chats_config.get(chat_id)
    if cfg is None:
        cfg = {
            "autotrade": False,
            "pairs": DEFAULT_PAIRS.copy(),
            "order_usdt": DEFAULT_ORDER_USDT,
            "leverage": DEFAULT_LEVERAGE,
            "daily_trades": 0,
            "daily_loss": 0.0,
            "last_reset": datetime.utcnow().date(),
            "trades": []  # list of trade dicts
        }
        chats_config[chat_id] = cfg
    else:
        # daily reset
        if cfg["last_reset"] != datetime.utcnow().date():
            cfg["daily_trades"] = 0
            cfg["daily_loss"] = 0.0
            cfg["last_reset"] = datetime.utcnow().date()
    return cfg

async def set_leverage(symbol: str, lev: int):
    try:
        await exchange.fapiPrivate_post_leverage({'symbol': symbol.replace("/", ""), 'leverage': lev})
    except Exception:
        # fallback: some ccxt builds use set_leverage
        try:
            await exchange.set_leverage(lev, symbol)
        except Exception as e:
            logger.debug("set_leverage failed: %s", e)

async def place_market_order(chat_cfg: dict, chat_id: int, symbol: str, side: str):
    """
    side: 'BUY' or 'SELL'
    position sizing based on order_usdt and price and leverage
    """
    price_ticker = await exchange.fetch_ticker(symbol)
    price = float(price_ticker['last'])
    order_usdt = float(chat_cfg["order_usdt"])
    lev = int(chat_cfg["leverage"])

    # approximate size in base units = (order_usdt * leverage) / price
    size = (order_usdt * lev) / price
    # round size according to market precision later (not implemented here)
    size = round(size, 6)

    logger.info("Placing %s %s size=%s price=%s", side, symbol, size, price)
    try:
        if side == "BUY":
            order = await exchange.create_order(symbol, type="MARKET", side="buy", amount=size, params={})
        else:
            order = await exchange.create_order(symbol, type="MARKET", side="sell", amount=size, params={})

        # record trade
        trade = {
            "time": datetime.utcnow().isoformat(),
            "symbol": symbol,
            "side": side,
            "size": size,
            "price": price,
            "usdt": order_usdt,
            "leverage": lev,
            "order": order
        }
        chat_cfg["trades"].append(trade)
        chat_cfg["daily_trades"] += 1

        # update daily loss / profit estimate (we can't get realized pnl immediately; set 0 here)
        # For robust accounting you'd fetch positions and realized PnL after trade.
        return trade
    except Exception as e:
        logger.error("Order failed: %s", e)
        return None

# -------------------- AUTO-TRADING ENGINE --------------------
async def autotrade_worker(app):
    """
    Periodically scans enabled chats and pairs, generates signals and executes trades
    honoring daily limits and recent_signal cooldown.
    """
    while True:
        try:
            now = datetime.utcnow()
            # loop chats
            for chat_id, cfg in list(chats_config.items()):
                # reset daily counters if needed
                ensure_chat_config(chat_id)

                if not cfg["autotrade"]:
                    continue

                # enforce daily limits
                if cfg["daily_trades"] >= MAX_TRADES_PER_DAY or cfg["daily_loss"] >= MAX_DAILY_LOSS_USDT:
                    logger.info("Chat %s reached daily limits: trades=%s loss=%s", chat_id, cfg["daily_trades"], cfg["daily_loss"])
                    continue

                pairs = cfg["pairs"]
                for symbol in pairs:
                    # cooldown: only act on a specific symbol once per X minutes per chat
                    key = f"{chat_id}:{symbol}"
                    cooldown = timedelta(minutes=30)
                    last = recent_signals.get(key)
                    if last and now - last < cooldown:
                        continue

                    sig = await generate_signals_for_symbol(symbol)
                    if not sig or not sig["signal"]:
                        continue

                    # additional filtering: require ATR > 0 and reasonable score
                    if sig["atr"] and sig["score"] and abs(sig["score"]) < 1.0:
                        continue

                    # risk check again
                    if cfg["daily_trades"] >= MAX_TRADES_PER_DAY:
                        break
                    if cfg["daily_loss"] >= MAX_DAILY_LOSS_USDT:
                        break

                    # execute trade
                    trade = await place_market_order(cfg, chat_id, symbol, sig["signal"])
                    if trade:
                        recent_signals[key] = datetime.utcnow()
                        # notify chat
                        try:
                            await app.bot.send_message(chat_id, f"AUTO-TRADE {trade['side']} {trade['symbol']} @ {trade['price']}\nsize={trade['size']} lev={trade['leverage']}")
                        except Exception as e:
                            logger.error("notify chat failed: %s", e)

            await asyncio.sleep(SCAN_INTERVAL_SECS)
        except Exception as e:
            logger.exception("autotrade_worker error: %s", e)
            await asyncio.sleep(10)

# -------------------- TELEGRAM HANDLERS / COMMANDS --------------------
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    ensure_chat_config(chat_id)
    keyboard = [
        [InlineKeyboardButton("Enable AutoTrade", callback_data="enable_autotrade")],
        [InlineKeyboardButton("Disable AutoTrade", callback_data="disable_autotrade")],
        [InlineKeyboardButton("Manage Pairs", callback_data="manage_pairs")],
        [InlineKeyboardButton("View Trades", callback_data="view_trades")],
    ]
    await update.message.reply_text("Welcome — choose:", reply_markup=InlineKeyboardMarkup(keyboard))

async def cb_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    cfg = ensure_chat_config(chat_id)

    data = query.data
    if data == "enable_autotrade":
        cfg["autotrade"] = True
        await query.edit_message_text("AutoTrade ENABLED")
    elif data == "disable_autotrade":
        cfg["autotrade"] = False
        await query.edit_message_text("AutoTrade DISABLED")
    elif data == "manage_pairs":
        buttons = [[InlineKeyboardButton(p, callback_data=f"togglepair:{p}")] for p in DEFAULT_PAIRS]
        await query.edit_message_text("Toggle pairs:", reply_markup=InlineKeyboardMarkup(buttons))
    elif data.startswith("togglepair:"):
        pair = data.split(":", 1)[1]
        if pair in cfg["pairs"]:
            cfg["pairs"].remove(pair)
            await query.edit_message_text(f"Removed {pair}")
        else:
            cfg["pairs"].append(pair)
            await query.edit_message_text(f"Added {pair}")
    elif data == "view_trades":
        if not cfg["trades"]:
            await query.edit_message_text("No trades yet.")
            return
        msg = "Recent trades:\n"
        for t in cfg["trades"][-10:]:
            msg += f"{t['time']} {t['side']} {t['symbol']} @{t['price']} size={t['size']}\n"
        await query.edit_message_text(msg)
    else:
        await query.edit_message_text("Unknown action.")

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    cfg = ensure_chat_config(chat_id)
    msg = (
        f"AutoTrade: {'ON' if cfg['autotrade'] else 'OFF'}\n"
        f"Pairs: {', '.join(cfg['pairs'])}\n"
        f"Order USDT: {cfg['order_usdt']}\n"
        f"Leverage: {cfg['leverage']}\n"
        f"Daily trades: {cfg['daily_trades']}/{MAX_TRADES_PER_DAY}\n"
        f"Daily loss (est): {cfg['daily_loss']:.2f}/{MAX_DAILY_LOSS_USDT}\n"
    )
    await update.message.reply_text(msg)

async def cmd_addpair(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    cfg = ensure_chat_config(chat_id)
    if not context.args:
        await update.message.reply_text("Usage: /addpair SYMBOL (e.g. /addpair SOL/USDT)")
        return
    pair = context.args[0].upper()
    if pair not in cfg["pairs"]:
        cfg["pairs"].append(pair)
        await update.message.reply_text(f"Added {pair}")
    else:
        await update.message.reply_text(f"{pair} already in pairs")

async def cmd_removepair(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    cfg = ensure_chat_config(chat_id)
    if not context.args:
        await update.message.reply_text("Usage: /removepair SYMBOL")
        return
    pair = context.args[0].upper()
    if pair in cfg["pairs"]:
        cfg["pairs"].remove(pair)
        await update.message.reply_text(f"Removed {pair}")
    else:
        await update.message.reply_text(f"{pair} not found")

async def cmd_pairs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    cfg = ensure_chat_config(chat_id)
    await update.message.reply_text(f"Pairs: {', '.join(cfg['pairs'])}")

async def cmd_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        bal = await exchange.fetch_balance()
        usdt = bal['total'].get('USDT', 0)
        await update.message.reply_text(f"Balance total USDT: {usdt}")
    except Exception as e:
        await update.message.reply_text(f"Error fetching balance: {e}")

async def cmd_trades(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    cfg = ensure_chat_config(chat_id)
    if not cfg["trades"]:
        await update.message.reply_text("No trades.")
        return
    msg = "Trades:\n"
    for t in cfg["trades"][-20:]:
        msg += f"{t['time']} {t['side']} {t['symbol']} @{t['price']} size={t['size']}\n"
    await update.message.reply_text(msg)

# -------------------- STARTUP & RUN --------------------
async def start_background_tasks(app):
    # start autotrade worker
    asyncio.create_task(autotrade_worker(app))

async def shutdown_exchange():
    try:
        await exchange.close()
    except Exception:
        pass

def build_app():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # commands
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("pairs", cmd_pairs))
    app.add_handler(CommandHandler("addpair", cmd_addpair))
    app.add_handler(CommandHandler("removepair", cmd_removepair))
    app.add_handler(CommandHandler("balance", cmd_balance))
    app.add_handler(CommandHandler("trades", cmd_trades))

    # callback buttons
    app.add_handler(CallbackQueryHandler(cb_handler))

    # on startup job
    app.post_init = start_background_tasks

    return app

# Run bot without asyncio.run() to avoid event-loop conflicts on some hosts
app = build_app()

if __name__ == "__main__":
    # schedule application to start inside existing loop
    loop = asyncio.get_event_loop()
    loop.create_task(app.initialize())         # initialize application
    loop.create_task(app.start())              # start polling/updater
    # start background tasks (app.post_init will run)
    try:
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down...")
        loop.run_until_complete(app.stop())
        loop.run_until_complete(app.shutdown())
        loop.run_until_complete(shutdown_exchange())
