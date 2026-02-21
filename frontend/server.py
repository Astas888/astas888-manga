"""
frontend/server.py
FastAPI backend for Astas888 Manga v2
Handles downloads, job management, and serves the dashboard UI.
"""

import os
import json
import uuid
import redis.asyncio as aioredis
from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from downloader.async_manager import AsyncDownloadManager
from scrapers.manga import scrape_manga, validate_manga_url
from scrapers.chapter import scrape_chapter_images

# -------------------------------------------------------
# 🚀 App Initialization
# -------------------------------------------------------

app = FastAPI(title="Astas888 Manga v2", version="2.0.0")
app.state.manager = AsyncDownloadManager()

# Directory where frontend files live
frontend_dir = os.path.join(os.path.dirname(__file__), "")
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")


# -------------------------------------------------------
# 🧠 Startup & Health
# -------------------------------------------------------

@app.on_event("startup")
async def startup():
    """Initialize Redis connection on startup."""
    app.state.redis = aioredis.from_url("redis://redis:6379/0", decode_responses=True)
    print("✅ Redis connected.")


@app.get("/health")
async def health():
    """Simple health check for Docker and monitoring."""
    return {"status": "ok"}


# -------------------------------------------------------
# ⚙️ API: Source Status
# -------------------------------------------------------

@app.get("/api/v1/settings/source-status")
async def get_source_status():
    """Return per-source download statistics."""
    r = app.state.redis
    keys = await r.keys("dl_stats:*:success")

    results = []
    for key in keys:
        src = key.split(":")[1]
        succ = int(await r.get(f"dl_stats:{src}:success") or 0)
        err = int(await r.get(f"dl_stats:{src}:error") or 0)
        limit = int(await r.get(f"dl_limit:{src}") or 3)
        total = succ + err
        rate = round((err / total * 100), 1) if total else 0
        results.append({
            "source": src,
            "limit": limit,
            "success": succ,
            "error": err,
            "error_rate": rate,
        })
    return results


# -------------------------------------------------------
# 📥 API: Download Trigger
# -------------------------------------------------------

@app.post("/api/v1/download")
async def trigger_download(data: dict = Body(...)):
    """
    Start a new manga or chapter download.
    Body: {"url": "https://mangapill.com/manga/one-piece"}
    """
    url = data.get("url")
    if not url:
        raise HTTPException(400, "Missing 'url'")

    if not validate_manga_url(url):
        raise HTTPException(400, "Invalid or unsupported URL")

    # Scrape metadata
    manga_data = scrape_manga(url)
    if not manga_data or not manga_data["chapters"]:
        raise HTTPException(400, "Could not fetch chapters.")

    # Create a job ID
    job_id = str(uuid.uuid4())
    job_data = {
        "id": job_id,
        "url": url,
        "title": manga_data["title"],
        "total_chapters": len(manga_data["chapters"]),
        "status": "queued"
    }

    # Push to Redis queue
    r = app.state.redis
    await r.set(f"job:{job_id}", json.dumps(job_data))
    await r.lpush("download_jobs", json.dumps(job_data))

    return {"message": f"Download started for {manga_data['title']}", "job_id": job_id}


# -------------------------------------------------------
# 📊 API: Job Progress
# -------------------------------------------------------

@app.get("/api/v1/progress/{job_id}")
async def get_progress(job_id: str):
    """Return progress for a given download job."""
    r = app.state.redis
    job_data = await r.get(f"job:{job_id}")
    if not job_data:
        raise HTTPException(404, "Job not found")

    job = json.loads(job_data)
    prog = await r.get(f"progress:{job_id}") or "0"
    job["progress"] = int(prog)
    return job


# -------------------------------------------------------
# 🕓 API: Completed/History
# -------------------------------------------------------

@app.get("/api/v1/history")
async def get_history():
    """Return all completed or failed jobs."""
    r = app.state.redis
    keys = await r.keys("job:*")
    results = []
    for key in keys:
        job = json.loads(await r.get(key))
        if job["status"] in ("completed", "failed"):
            results.append(job)
    return sorted(results, key=lambda j: j.get("title", ""))


# -------------------------------------------------------
# ❌ API: Cancel Download
# -------------------------------------------------------

@app.post("/api/v1/cancel/{job_id}")
async def cancel_download(job_id: str):
    """Cancel a running or queued job."""
    r = app.state.redis
    job_data = await r.get(f"job:{job_id}")
    if not job_data:
        raise HTTPException(404, "Job not found")

    job = json.loads(job_data)
    job["status"] = "cancelled"
    await r.set(f"job:{job_id}", json.dumps(job))
    return {"message": f"Job {job_id} cancelled"}


# -------------------------------------------------------
# 🧭 Frontend serving (Dashboard)
# -------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serve the Vue dashboard (index.html) at the root path."""
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h1>Astas888 Manga API</h1><p>Frontend not found.</p>", status_code=404)

# -------------------------------------------------------
# 🔍 Search API
# -------------------------------------------------------

@app.get("/api/v1/search")
async def search_manga(q: str):
    """
    Search available sources for a manga title.
    Example: /api/v1/search?q=one%20piece
    """
    from sources import find_source_for_url
    results = []

    # For now only Mangapill; more sources can be looped here
    base = "https://mangapill.com"
    search_url = f"{base}/search?q={q.replace(' ', '+')}"
    import httpx
    from bs4 import BeautifulSoup

    async with httpx.AsyncClient() as client:
        resp = await client.get(search_url)
        soup = BeautifulSoup(resp.text, "html.parser")
        for a in soup.select("a[href^='/manga/']"):
            title = a.text.strip()
            href = a.get("href")
            if href and title:
                results.append({
                    "title": title,
                    "url": base + href,
                    "source": "mangapill"
                })

    return results


# -------------------------------------------------------
# ⚙️ Manage Sources
# -------------------------------------------------------

@app.get("/api/v1/sources")
async def get_sources():
    """Return active sources."""
    r = app.state.redis
    raw = await r.get("sources")
    return json.loads(raw) if raw else ["mangapill"]

@app.post("/api/v1/sources")
async def add_source(data: dict = Body(...)):
    """Add a new source dynamically."""
    r = app.state.redis
    src = data.get("name")
    if not src:
        raise HTTPException(400, "Missing source name")
    current = json.loads(await r.get("sources") or "[]")
    if src not in current:
        current.append(src)
        await r.set("sources", json.dumps(current))
    return {"sources": current}

@app.delete("/api/v1/sources/{name}")
async def remove_source(name: str):
    """Remove a source by name."""
    r = app.state.redis
    current = json.loads(await r.get("sources") or "[]")
    current = [s for s in current if s != name]
    await r.set("sources", json.dumps(current))
    return {"sources": current}
