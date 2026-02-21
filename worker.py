import asyncio
import redis.asyncio as aioredis
from downloader.async_manager import AsyncDownloadManager

async def main():
    redis = aioredis.from_url("redis://redis:6379/0", decode_responses=True)
    mgr = AsyncDownloadManager()
    while True:
        job = await redis.blpop("download_jobs", timeout=5)
        if not job:
            await asyncio.sleep(1)
            continue
        data = eval(job[1])
        await mgr.download_chapter(**data)

if __name__ == "__main__":
    asyncio.run(main())
