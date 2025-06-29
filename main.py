
import requests
import time
import telegram
from datetime import datetime, timedelta
from telegram.ext import CommandHandler, Updater

TELEGRAM_TOKEN = '7933133710:AAExJMA4RWv8bGyx7vOcA9qSUzm5JlFiAow'
CHAT_ID = None
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
PRICE_THRESHOLD = 1.0
OI_THRESHOLD = 5.0

bot = telegram.Bot(token=TELEGRAM_TOKEN)
print("✅ Бот запущен")

updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
dispatcher = updater.dispatcher

def start(update, context):
    global CHAT_ID
    CHAT_ID = update.effective_chat.id
    context.bot.send_message(chat_id=CHAT_ID, text="✅ Бот запущен. Используй команды: /status, /symbols, /set_price, /set_oi")

def status(update, context):
    msg = f"📊 Настройки:\nМонеты: {', '.join(SYMBOLS)}\nПорог цены: {PRICE_THRESHOLD}%\nПорог OI: {OI_THRESHOLD}%"
    context.bot.send_message(chat_id=update.effective_chat.id, text=msg)

def set_price(update, context):
    global PRICE_THRESHOLD
    try:
        PRICE_THRESHOLD = float(context.args[0])
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"✅ Новый порог цены: {PRICE_THRESHOLD}%")
    except:
        context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ Укажи число, например: /set_price 2.5")

def set_oi(update, context):
    global OI_THRESHOLD
    try:
        OI_THRESHOLD = float(context.args[0])
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"✅ Новый порог OI: {OI_THRESHOLD}%")
    except:
        context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ Укажи число, например: /set_oi 4.0")

def symbols(update, context):
    global SYMBOLS
    if context.args:
        SYMBOLS = [s.upper() for s in context.args]
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"✅ Обновлён список монет: {', '.join(SYMBOLS)}")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ Укажи символы, например: /symbols BTCUSDT ETHUSDT")

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("status", status))
dispatcher.add_handler(CommandHandler("set_price", set_price))
dispatcher.add_handler(CommandHandler("set_oi", set_oi))
dispatcher.add_handler(CommandHandler("symbols", symbols))

updater.start_polling()

def get_funding_rate(symbol):
    url = f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={symbol}&limit=1"
    r = requests.get(url).json()
    if r:
        return float(r[0]['fundingRate']) * 100
    return 0

def get_price_change(symbol):
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval=5m&limit=2"
    r = requests.get(url).json()
    if len(r) >= 2:
        old_price = float(r[-2][4])
        new_price = float(r[-1][4])
        change = (new_price - old_price) / old_price * 100
        return change, new_price
    return 0, 0

OI_CACHE = {}
def get_open_interest_change(symbol):
    url = f"https://fapi.binance.com/fapi/v1/openInterest?symbol={symbol}"
    r = requests.get(url).json()
    current_oi = float(r['openInterest'])
    old_oi = OI_CACHE.get(symbol, current_oi)
    OI_CACHE[symbol] = current_oi
    change = (current_oi - old_oi) / old_oi * 100 if old_oi != 0 else 0
    return change

def get_volume(symbol):
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval=5m&limit=1"
    r = requests.get(url).json()
    if r:
        return float(r[0][5])
    return 0

while True:
    for symbol in SYMBOLS:
        try:
            price_change, price = get_price_change(symbol)
            oi_change = get_open_interest_change(symbol)
            volume = get_volume(symbol)
            funding = get_funding_rate(symbol)

            if price_change >= PRICE_THRESHOLD and oi_change >= OI_THRESHOLD:
                msg = f"\n🚨 <b>{symbol}</b> сигнал!\n" \
                      f"Цена: <b>{price:.2f}$</b> ({price_change:+.2f}%)\n" \
                      f"Open Interest: <b>{oi_change:+.2f}%</b>\n" \
                      f"Объём (5м): <b>{volume:.2f}</b>\n" \
                      f"Funding Rate: <b>{funding:.4f}%</b>\n"
                if CHAT_ID:
                    bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='HTML')
        except Exception as e:
            print(f"Ошибка для {symbol}: {e}")
    time.sleep(60)
