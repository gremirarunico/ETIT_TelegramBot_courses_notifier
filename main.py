#!/usr/bin/env python3

import json
import hashlib
import telegram
import asyncio
from app import App


async def send_data(tg):
    while True:
        await asyncio.sleep(5)

async def main():
    tg = telegram.Telegram('config.json', 'telegram_data.json')
    await tg.start()

    app = App('courses_data.json', tg)
    await app.start()

    # Forever loop
    while True:
        await asyncio.sleep(1)

if __name__ == '__main__':
    asyncio.run(main())