import os
import logging
import asyncio
import ccxt
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)

# Load API keys from environment
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Set up Binance futures testnet
exchange = ccxt.binance({
    "apiKey": BINANCE_API_KEY,
    "secret": BINANCE_API_SECRET,
    "options": {
        "defaultType": "future"
    }
})

# ---------------- COMMANDS ---------------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Bot is LIVE ✅\n\nCommands:\n/start\n/price BTC/USDT\n/buy\n/sell"
    )

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = context.args[0] if context.args else "BTC/USDT"
    symbol = symbol.upper()

    ticker = exchange.fetch_ticker(symbol)
    await update.message.reply_text(f"Price of {symbol}: {ticker['last']}")

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = "BTC/USDT"
    order = exchange.create_market_buy_order(symbol, 0.001)
    await update.message.reply_text(f"BUY order placed:\n{order}")

async def sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = "BTC/USDT"
    order = exchange.create_market_sell_order(symbol, 0.001)
    await update.message.reply_text(f"SELL order placed:\n{order}")

# ---------------- MAIN ENTRY ---------------- #

async def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("sell", sell))

    print("Bot is running...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
