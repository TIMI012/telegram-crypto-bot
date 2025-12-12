import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import ccxt

logging.basicConfig(level=logging.INFO)

# Load environment variables
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Debug: confirm token loaded
if TELEGRAM_BOT_TOKEN is None:
    raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables!")

# Initialize Binance exchange (Testnet or Mainnet)
exchange = ccxt.binance({
    "apiKey": API_KEY,
    "secret": API_SECRET,
    "options": {"defaultType": "future"}  # Futures trading
})

# Telegram bot commands
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

# Main: build and run the bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("sell", sell))

    # Proper polling for Render, avoids "event loop already running" error
    app.run_polling()
async def main():
    print("Loaded token:", TELEGRAM_BOT_TOKEN is not None)  # Debug: True means token loaded
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("sell", sell))

    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
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
