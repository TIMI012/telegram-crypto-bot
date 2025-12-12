import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import ccxt
import asyncio

logging.basicConfig(level=logging.INFO)

# Load environment variables
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

print("Loaded token:", TELEGRAM_BOT_TOKEN)

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
    order = exchange.create_market_buy_order("BTC/USDT", 0.001)
    await update.message.reply_text(str(order))

async def sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    order = exchange.create_market_sell_order("BTC/USDT", 0.001)
    await update.message.reply_text(str(order))

async def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("sell", sell))

    print("Bot is running...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    # Keep process alive forever
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
