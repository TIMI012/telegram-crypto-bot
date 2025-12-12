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

# Debug print to verify environment variables
print("Loaded TELEGRAM_BOT_TOKEN:", TELEGRAM_BOT_TOKEN)

# Binance testnet setup
exchange = ccxt.binance({
    "apiKey": API_KEY,
    "secret": API_SECRET,
    "options": {"defaultType": "future"},
})
exchange.set_sandbox_mode(True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is live! Use /price BTC/USDT to check price.")


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
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("sell", sell))

    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /price BTC/USDT")
        return

    symbol = context.args[0].upper()

    try:
        ticker = exchange.fetch_ticker(symbol)
        await update.message.reply_text(f"{symbol} Price: {ticker['last']}")
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

# ===============================
# /buy COMMAND
# ===============================
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /buy BTC/USDT 10")
        return

    symbol = context.args[0].upper()
    amount = float(context.args[1])

    try:
        order = exchange.create_market_buy_order(symbol, amount)
        await update.message.reply_text(f"Bought {amount} of {symbol}\n\n{order}")
    except Exception as e:
        await update.message.reply_text(f"Buy Failed: {str(e)}")

# ===============================
# /sell COMMAND
# ===============================
async def sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /sell BTC/USDT 10")
        return

    symbol = context.args[0].upper()
    amount = float(context.args[1])

    try:
        order = exchange.create_market_sell_order(symbol, amount)
        await update.message.reply_text(f"Sold {amount} of {symbol}\n\n{order}")
    except Exception as e:
        await update.message.reply_text(f"Sell Failed: {str(e)}")

# ===============================
# MAIN
# ===============================
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("sell", sell))

    print("Bot is running...")
    app.run_polling()        ticker = exchange.fetch_ticker(symbol)
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
    logging.info("Starting Telegram bot...")
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Register command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("sell", sell))

    # Run polling (Background Worker handles event loop)
    app.run_polling()        ticker = exchange.fetch_ticker(symbol)
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
