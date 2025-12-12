import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import ccxt
import asyncio

logging.basicConfig(level=logging.INFO)

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

exchange = ccxt.binance({
    "apiKey": API_KEY,
    "secret": API_SECRET,
    "options": {"defaultType": "future"}
})

alert_subscribers = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📈 Price", callback_data="price_menu")],
        [InlineKeyboardButton("🟢 Buy BTC", callback_data="buy_btc")],
        [InlineKeyboardButton("🔴 Sell BTC", callback_data="sell_btc")],
        [InlineKeyboardButton("💰 Balance", callback_data="balance")],
        [InlineKeyboardButton("📊 PnL", callback_data="pnl")],
        [InlineKeyboardButton("⏰ Toggle Alerts", callback_data="toggle_alerts")]
    ]
    await update.message.reply_text("Choose an option:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    chat_id = query.message.chat_id

    await query.answer()

    if data == "toggle_alerts":
        if chat_id in alert_subscribers:
            alert_subscribers.remove(chat_id)
            await query.edit_message_text("🔕 Alerts turned OFF")
        else:
            alert_subscribers.add(chat_id)
            await query.edit_message_text("🔔 Alerts turned ON")
        return

    if data == "balance":
        balance = exchange.fetch_balance()
        usdt = balance['total'].get('USDT', 0)
        await query.edit_message_text(f"💰 Balance: {usdt} USDT")
        return

async def run_alerts(app):
    while True:
        if alert_subscribers:
            ticker = exchange.fetch_ticker("BTC/USDT")
            price = ticker["last"]
            for chat_id in list(alert_subscribers):
                try:
                    await app.bot.send_message(chat_id, f"⏰ BTC Price: {price}")
                except:
                    pass
        await asyncio.sleep(3600)  # every 1 hour

async def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    # run alerts in background
    app.job_queue.run_once(lambda *_: asyncio.create_task(run_alerts(app)), 1)

    await app.run_polling(close_loop=False)

if __name__ == "__main__":
    asyncio.get_event_loop().create_task(main())
    asyncio.get_event_loop().run_forever()        [InlineKeyboardButton("⏰ Toggle Alerts", callback_data="toggle_alerts")]
    ]
    await update.message.reply_text("Choose an option:", reply_markup=InlineKeyboardMarkup(keyboard))


# ---------- INLINE BUTTON HANDLER ----------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    chat_id = query.message.chat_id

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
            usdt = balance["total"].get("USDT", 0)
            btc = balance["total"].get("BTC", 0)
            await query.edit_message_text(f"USDT: {usdt}\nBTC: {btc}")

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
                await query.edit_message_text("⏰ Alerts DISABLED")
            else:
                alert_subscribers.add(chat_id)
                await query.edit_message_text("⏰ Alerts ENABLED")

    except Exception as e:
        await query.edit_message_text(f"Error: {e}")


# ---------- COMMANDS ----------
async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = (context.args[0] if context.args else "BTC/USDT").upper()
    ticker = exchange.fetch_ticker(symbol)
    await update.message.reply_text(f"Price of {symbol}: {ticker['last']}")


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    b = exchange.fetch_balance()
    usdt = b["total"].get("USDT", 0)
    btc = b["total"].get("BTC", 0)
    await update.message.reply_text(f"Balance:\nUSDT: {usdt}\nBTC: {btc}")


async def pnl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    positions = exchange.fetch_positions()
    text = "PnL Report:\n\n"
    for p in positions:
        if p["contracts"] > 0:
            text += f"{p['symbol']} → {p['unrealizedPnl']}\n"
    await update.message.reply_text(text)


# ---------- BACKGROUND ALERTS ----------
async def price_alert_job(app):
    while True:
        if alert_subscribers:
            try:
                ticker = exchange.fetch_ticker("BTC/USDT")
                price = ticker["last"]
                for chat_id in alert_subscribers:
                    await app.bot.send_message(chat_id, f"⏰ BTC Price Alert: {price}")
            except Exception as e:
                logging.error("Alert error: %s", e)

        await asyncio.sleep(3600)  # every 1 hour


# ---------- MAIN ----------
async def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("pnl", pnl))
    app.add_handler(CallbackQueryHandler(button_handler))

    asyncio.create_task(price_alert_job(app))

    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
