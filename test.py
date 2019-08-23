import asyncio
import time

import aiohttp

async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()


async def main():
    async with aiohttp.ClientSession() as session:
        html = await fetch(session, 'http://127.0.0.1:8686/api/order/put')
        print(html)
ts = time.time()
tasks = []
for i in range(2000):
    tasks.append(asyncio.ensure_future(main()))

loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.wait(tasks))
print(time.time() - ts)

# 线程模式
# import requests
# import threading
#
# def fetch(url):
#     response = requests.get(url)
#     print(response.text)
#
# for i in range(2000):
#     threading.Thread(target=fetch, args=('http://127.0.0.1:8686/api/order/put',)).start()