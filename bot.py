import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import ccxt

# Logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

if not TELEGRAM_BOT_TOKEN or not API_KEY or not API_SECRET:
    raise ValueError("Missing required environment variables!")

# Binance exchange config (Testnet by default)
USE_TESTNET = True  # Set to False to go live on mainnet
exchange = ccxt.binance({
    "apiKey": API_KEY,
    "secret": API_SECRET,
    "options": {"defaultType": "future"},
    "urls": {"api": "https://testnet.binancefuture.com" if USE_TESTNET else None}
})

# --- Telegram command handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Bot is live! Use /price BTC/USDT to check price.\n"
        "Use /buy or /sell to simulate trades on Testnet."
    )

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = (context.args[0] if context.args else "BTC/USDT").upper()
    try:
        ticker = exchange.fetch_ticker(symbol)
        await update.message.reply_text(f"💰 Price of {symbol}: {ticker['last']}")
    except Exception as e:
        await update.message.reply_text(f"Error fetching price: {e}")

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = "BTC/USDT"
    try:
        order = exchange.create_market_buy_order(symbol, 0.001)
        await update.message.reply_text(f"✅ Bought: {order}")
    except Exception as e:
        await update.message.reply_text(f"Error buying: {e}")

async def sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = "BTC/USDT"
    try:
        order = exchange.create_market_sell_order(symbol, 0.001)
        await update.message.reply_text(f"✅ Sold: {order}")
    except Exception as e:
        await update.message.reply_text(f"Error selling: {e}")

# --- Run Bot ---
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Register command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("sell", sell))

    # Poll Telegram (Background Worker handles event loop)
    logging.info("Bot is starting...")
    app.run_polling()    await update.message.reply_text(f"Bought: {order}")

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
