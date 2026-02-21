import os, asyncio, httpx, random
from pathlib import Path
import redis.asyncio as aioredis
from rich.console import Console
from constants import HEADERS, DEFAULT_REQUEST_TIMEOUT
from config import get_config
from sources import find_source_for_url
from PIL import Image

console = Console()

class AsyncDownloadManager:
    def __init__(self, config=None):
        self.config = config or get_config()
        self.output_dir = Path(self.config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.client = httpx.AsyncClient(
            timeout=DEFAULT_REQUEST_TIMEOUT,
            limits=httpx.Limits(max_connections=50, max_keepalive_connections=20),
            headers=HEADERS,
        )
        self.redis = None
        self.default_limit = int(os.getenv("DL_GLOBAL_LIMIT", 3))
        self.compress_images = os.getenv("COMPRESS_IMAGES", "false").lower() == "true"

    async def connect_redis(self):
        if self.redis is None:
            self.redis = aioredis.from_url(
                os.getenv("REDIS_URL", "redis://redis:6379/0"),
                decode_responses=True,
            )

    async def _record_result(self, source, success: bool):
        await self.connect_redis()
        base = f"dl_stats:{source.lower()}"
        if success:
            await self.redis.incr(f"{base}:success")
        else:
            await self.redis.incr(f"{base}:error")

        if random.random() < 0.1:
            succ = int(await self.redis.get(f"{base}:success") or 0)
            err = int(await self.redis.get(f"{base}:error") or 0)
            if succ + err > 200:
                await self.redis.set(f"{base}:success", succ // 2)
                await self.redis.set(f"{base}:error", err // 2)
        await self._auto_adjust_limit(source)

    async def _get_limit(self, source):
        await self.connect_redis()
        key = f"dl_limit:{source.lower()}"
        val = await self.redis.get(key)
        return int(val) if val else self.default_limit

    async def _set_limit(self, source, val):
        await self.connect_redis()
        await self.redis.set(f"dl_limit:{source.lower()}", val)

    async def _auto_adjust_limit(self, source):
        succ = int(await self.redis.get(f"dl_stats:{source}:success") or 0)
        err = int(await self.redis.get(f"dl_stats:{source}:error") or 0)
        total = succ + err
        if total < 10:
            return
        current = await self._get_limit(source)
        rate = err / total
        if rate > 0.3 and current > 1:
            new = current - 1
            await self._set_limit(source, new)
            console.log(f"⚠️ Backoff {source}: error {rate:.0%}, limit {current}->{new}")
        elif rate < 0.05 and current < 10:
            new = current + 1
            await self._set_limit(source, new)
            console.log(f"✅ Raise {source} limit {current}->{new}")

    async def _acquire_slot(self, source):
        await self.connect_redis()
        key = f"dl_active:{source.lower()}"
        while True:
            limit = await self._get_limit(source)
            active = int(await self.redis.get(key) or 0)
            if active < limit:
                await self.redis.incr(key)
                return
            await asyncio.sleep(1)

    async def _release_slot(self, source):
        await self.connect_redis()
        await self.redis.decr(f"dl_active:{source.lower()}")

    async def download_chapter(self, manga_title, chapter_title, urls, source_url=None, sem_limit=8):
        source = getattr(find_source_for_url(source_url or ""), "name", "global").lower()
        await self._acquire_slot(source)
        try:
            folder = self.output_dir / manga_title / chapter_title
            folder.mkdir(parents=True, exist_ok=True)
            sem = asyncio.Semaphore(sem_limit)
            total, done = len(urls), 0

            async def save(i, url):
                nonlocal done
                ext = Path(url).suffix or ".jpg"
                dest = folder / f"{i:03d}{ext}"
                if dest.exists() and dest.stat().st_size > 0:
                    return
                try:
                    async with sem, self.client.stream("GET", url) as r:
                        r.raise_for_status()
                        with open(dest, "wb") as f:
                            async for chunk in r.aiter_bytes():
                                f.write(chunk)
                    if self.compress_images:
                        img = Image.open(dest).convert("RGB")
                        img.save(dest, "JPEG", quality=85, optimize=True)
                    done += 1
                    await self._record_result(source, True)
                except Exception as e:
                    console.log(f"❌ {url}: {e}")
                    await self._record_result(source, False)

            await asyncio.gather(*(save(i, u) for i, u in enumerate(urls, 1)))
            console.log(f"✅ {source} {manga_title} {chapter_title}: {done}/{total}")
        finally:
            await self._release_slot(source)
