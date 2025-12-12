import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import ccxt

logging.basicConfig(level=logging.INFO)

# -------- CONFIG --------
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Currency pairs to track
CURRENCY_PAIRS = ["BTC/USDT", "ETH/USDT", "BNB/USDT"]

exchange = ccxt.binance({
    "apiKey": API_KEY,
    "secret": API_SECRET,
    "options": {"defaultType": "future"}
})

alert_subscribers = set()

# -------- COMMANDS --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📈 Price", callback_data="price_menu")],
        [InlineKeyboardButton("🟢 Buy BTC", callback_data="buy_btc")],
        [InlineKeyboardButton("🔴 Sell BTC", callback_data="sell_btc")],
        [InlineKeyboardButton("💰 Balance", callback_data="balance")],
        [InlineKeyboardButton("📊 PnL", callback_data="pnl")],
        [InlineKeyboardButton("⏰ Toggle Alerts", callback_data="toggle_alerts")]
    ]
    await update.message.reply_text(
        "Choose an option:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pair = context.args[0].upper() if context.args else "BTC/USDT"
    try:
        ticker = exchange.fetch_ticker(pair)
        await update.message.reply_text(f"Price of {pair}: {ticker['last']}")
    except Exception as e:
        await update.message.reply_text(f"Error fetching price for {pair}: {e}")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        b = exchange.fetch_balance()
        usdt = b["total"].get("USDT", 0)
        btc = b["total"].get("BTC", 0)
        await update.message.reply_text(f"Balance:\nUSDT: {usdt}\nBTC: {btc}")
    except Exception as e:
        await update.message.reply_text(f"Error fetching balance: {e}")

async def pnl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        positions = exchange.fetch_positions()
        text = "PnL Report:\n\n"
        for p in positions:
            if p["contracts"] > 0:
                text += f"{p['symbol']} → {p['unrealizedPnl']}\n"
        await update.message.reply_text(text)
    except Exception as e:
        await update.message.reply_text(f"Error fetching PnL: {e}")

# -------- BUTTON HANDLER --------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    data = query.data

    try:
        if data == "price_menu":
            text = ""
            for pair in CURRENCY_PAIRS:
                ticker = exchange.fetch_ticker(pair)
                text += f"{pair}: {ticker['last']}\n"
            await query.edit_message_text(text)

        elif data == "buy_btc":
            order = exchange.create_market_buy_order("BTC/USDT", 0.001)
            await query.edit_message_text(f"Bought BTC:\n{order}")

        elif data == "sell_btc":
            order = exchange.create_market_sell_order("BTC/USDT", 0.001)
            await query.edit_message_text(f"Sold BTC:\n{order}")

        elif data == "balance":
            b = exchange.fetch_balance()
            text = "\n".join([f"{k}: {v}" for k, v in b["total"].items()])
            await query.edit_message_text(f"Balance:\n{text}")

        elif data == "pnl":
            positions = exchange.fetch_positions()
            text = "PnL Report:\n\n"
            for p in positions:
                if p["contracts"] > 0:
                    text += f"{p['symbol']} → {p['unrealizedPnl']}\n"
            await query.edit_message_text(text)

        elif data == "toggle_alerts":
            if chat_id in alert_subscribers:
                alert_subscribers.remove(chat_id)
                await query.edit_message_text("🔕 Alerts OFF")
            else:
                alert_subscribers.add(chat_id)
                await query.edit_message_text("🔔 Alerts ON")

    except Exception as e:
        await query.edit_message_text(f"Error: {e}")

# -------- BACKGROUND ALERTS --------
async def price_alert_job(app: Application):
    while True:
        if alert_subscribers:
            for pair in CURRENCY_PAIRS:
                try:
                    ticker = exchange.fetch_ticker(pair)
                    price = ticker["last"]
                    for chat_id in alert_subscribers:
                        await app.bot.send_message(chat_id, f"⏰ {pair} Price Alert: {price}")
                except Exception as e:
                    logging.error("Alert error: %s", e)
        await asyncio.sleep(3600)  # 1 hour

# -------- MAIN --------
async def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("pnl", pnl))
    app.add_handler(CallbackQueryHandler(button_handler))

    # Run background alerts
    asyncio.create_task(price_alert_job(app))

    # Start polling (Render-safe)
    await app.run_polling(close_loop=False)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
