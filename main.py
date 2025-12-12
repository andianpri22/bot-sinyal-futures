import asyncio
import aiohttp
from datetime import datetime
import hashlib
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode

# GANTI 2 BARIS INI SAJA NANTI DI RENDER.COM
BOT_TOKEN = "TOKEN_BOT_KAMU_DISINI"
CHANNEL_ID = "@channelkamu"

bot = Bot(token=BOT_TOKEN)

WATCHLIST = ["BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT","DOGEUSDT","1000PEPEUSDT","WIFUSDT","BONKUSDT","AVAXUSDT","TONUSDT","SUIUSDT","ADAUSDT","LINKUSDT","BNBUSDT","TRXUSDT"]

checked = set()

async def fetch_binance():
    url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            return await r.json()

async def send_signal(symbol, side, entry, tp, sl, reason):
    signal_id = hashlib.md5(f"{symbol}{entry}".encode()).hexdigest()[:8]
    if signal_id in checked: return
    checked.add(signal_id)
    if len(checked)>500: checked.clear()

    caption = f"""
{Side} **{symbol.replace('USDT','')} {Side}**

Entry : `{entry}`
TP1 : `{tp[0]}`    TP3 : `{tp[2]}`
TP2 : `{tp[1]}`    TP4 : `{tp[3]}`
Stop  : `{sl}`

Leverage: 10-20x | {reason}
{datetime.now().strftime('%d %b %H:%M WIB')}
    """.strip()

    keyboard = InlineKeyboardMarkup([[ 
        InlineKeyboardButton("Binance Futures", url=f"https://binance.com/en/futures/{symbol}"),
        InlineKeyboardButton("TradingView", url=f"https://tradingview.com/symbols/{symbol}PERP/")
    ]])

    await bot.send_photo(
        chat_id=CHANNEL_ID,
        photo=f"https://www.binance.com/future/chart/png?symbol={symbol}&interval=5m&theme=DARK",
        caption=caption,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )

async def scanner():
    while True:
        try:
            data = await fetch_binance()
            ticker = {d['symbol']: d for d in data if d['symbol'] in WATCHLIST}
            for sym in WATCHLIST:
                if sym not in ticker: continue
                t = ticker[sym]
                change = float(t['priceChangePercent'])
                price = float(t['lastPrice'])
                vol = float(t['quoteVolume'])

                if vol < 20_000_000: continue

                if 11 < change < 50:
                    tp = [price*1.04, price*1.08, price*1.15, price*1.30]
                    await send_signal(sym,"LONG",f"{price:.5f}", [f"{x:.5f}" for x in tp], f"{price*0.92:.5f}", f"Pump {change:+.1f}%")

                if -40 < change < -10:
                    tp = [price*0.96, price*0.92, price*0.85, price*0.75]
                    await send_signal(sym,"SHORT",f"{price:.5f}", [f"{x:.5f}" for x in tp], f"{price*1.08:.5f}", f"Drop {change:+.1f}%")

            await asyncio.sleep(60)
        except Exception as e:
            print(e)
            await asyncio.sleep(60)

asyncio.run(scanner())
