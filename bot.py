import os
import time
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import ccxt

logging.basicConfig(level=logging.INFO)

API_KEY = os.getenv("ULuLlnqyzfVPZOL1UrJdSDZYpgSII4AdoQ0p4rBa2hLhbuagHqiw9VMOH7EAPt6E")
API_SECRET = os.getenv("vNVYGVoPg9jyEuori5EBLy1l7T5ZmIZGAtWkYTw9wjRxsivpvgi6kNwWTQrjiRZf")
TELEGRAM_BOT_TOKEN = os.getenv("8310267297:AAHAIaL40P6ppLCBzI5BFgNuCKuGgQ81WO0")

exchange = ccxt.binance({
    "apiKey": API_KEY,
    "secret": API_SECRET,
    "options": {"defaultType": "future"}
})

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is live. Use /price BTC/USDT to check price.")

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = (context.args[0] if context.args else "BTC/USDT").upper()
    ticker = exchange.fetch_ticker(symbol)
    await update.message.reply_text(f"Price of {symbol}: {ticker['last']}")

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = "BTC/USDT"
    order = exchange.create_market_buy_order(symbol, 0.001)
    await update.message.reply_text(f"Bought: {order}")

async def sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = "BTC/USDT"
    order = exchange.create_market_sell_order(symbol, 0.001)
    await update.message.reply_text(f"Sold: {order}")

async def main():
    print("Loaded token:", TELEGRAM_BOT_TOKEN)  # Debug line
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("sell", sell))

    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
