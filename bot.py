import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import ccxt
import asyncio

logging.basicConfig(level=logging.INFO)

# -------------------- ENV --------------------
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
YOUR_TELEGRAM_ID = int(os.getenv("YOUR_TELEGRAM_ID"))  # put your ID here or in env

exchange = ccxt.binance({
    "apiKey": API_KEY,
    "secret": API_SECRET,
    "options": {"defaultType": "future"}
})

ALERT_ON = False  # Background alert toggle


# -------------------- HANDLERS --------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📈 Price", callback_data="price_menu")],
        [InlineKeyboardButton("🟢 Buy BTC", callback_data="buy_btc")],
        [InlineKeyboardButton("🔴 Sell BTC", callback_data="sell_btc")],
        [InlineKeyboardButton("💰 Balance", callback_data="balance")],
        [InlineKeyboardButton("📊 PnL", callback_data="pnl")],
        [InlineKeyboardButton("⏰ Toggle Alerts", callback_data="toggle_alerts")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose an option:", reply_markup=reply_markup)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    try:
        if data == "price_menu":
            ticker = exchange.fetch_ticker("BTC/USDT")
            await query.edit_message_text(f"BTC Price: {ticker['last']}")

        elif data == "buy_btc":
            order = exchange.create_market_buy_order("BTC/USDT", 0.001)
            await query.edit_message_text(f"Bought BTC:\n{order}")

        elif data == "sell_btc":
            order = exchange.create_market_sell_order("BTC/USDT", 0.001)
            await query.edit_message_text(f"Sold BTC:\n{order}")

        elif data == "balance":
            balance = exchange.fetch_balance()
            usdt = balance["total"]["USDT"]
            btc = balance["total"]["BTC"]
            await query.edit_message_text(f"USDT: {usdt}\nBTC: {btc}")

        elif data == "pnl":
            positions = exchange.fetch_positions()
            text = "PnL Report:\n\n"
            for p in positions:
                if p['contracts'] > 0:
                    text += f"{p['symbol']} — PnL: {p['unrealizedPnl']}\n"
            await query.edit_message_text(text)

        elif data == "toggle_alerts":
            global ALERT_ON
            ALERT_ON = not ALERT_ON
            status = "ENABLED" if ALERT_ON else "DISABLED"
            await query.edit_message_text(f"⏰ Alerts {status}")
    except Exception as e:
        await query.edit_message_text(f"Error: {e}")


async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = (context.args[0] if context.args else "BTC/USDT").upper()
    ticker = exchange.fetch_ticker(symbol)
    await update.message.reply_text(f"Price of {symbol}: {ticker['last']}")


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    b = exchange.fetch_balance()
    usdt = b["total"]["USDT"]
    btc = b["total"]["BTC"]
    await update.message.reply_text(f"Balance:\nUSDT: {usdt}\nBTC: {btc}")


async def pnl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    positions = exchange.fetch_positions()
    text = "PnL Report:\n\n"
    for p in positions:
        if p["contracts"] > 0:
            text += f"{p['symbol']} — PnL: {p['unrealizedPnl']}\n"
    await update.message.reply_text(text)


# -------------------- BACKGROUND ALERT --------------------
async def price_alert_job(app):
    global ALERT_ON
    while True:
        if ALERT_ON:
            try:
                ticker = exchange.fetch_ticker("BTC/USDT")
                price = ticker["last"]
                await app.bot.send_message(YOUR_TELEGRAM_ID, f"⏰ BTC Price Alert: {price}")
            except Exception as e:
                logging.error("Alert error: %s", e)
        await asyncio.sleep(3600)  # 1 hour interval


# -------------------- MAIN --------------------
async def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("pnl", pnl))

    # Inline buttons
    app.add_handler(CallbackQueryHandler(button_handler))

    # Start background alert task
    app.job_queue.run_repeating(lambda _: price_alert_job(app), interval=3600, first=10)

    # Start polling
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
