from fastapi import FastAPI, Body
import redis.asyncio as aioredis
from downloader.async_manager import AsyncDownloadManager

app = FastAPI(title="Astas888 Manga v2")
app.state.manager = AsyncDownloadManager()

@app.on_event("startup")
async def startup():
    app.state.redis = aioredis.from_url("redis://redis:6379/0", decode_responses=True)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/api/v1/settings/source-status")
async def get_source_status():
    r = app.state.redis
    keys = await r.keys("dl_stats:*:success")
    results = []
    for key in keys:
        src = key.split(":")[1]
        succ = int(await r.get(f"dl_stats:{src}:success") or 0)
        err = int(await r.get(f"dl_stats:{src}:error") or 0)
        limit = int(await r.get(f"dl_limit:{src}") or 3)
        total = succ + err
        rate = round((err/total*100),1) if total else 0
        results.append({"source":src,"limit":limit,"success":succ,"error":err,"error_rate":rate})
    return results
