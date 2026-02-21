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

from fastapi import Query

@app.get("/api/v1/search")
async def search_manga(q: str = Query(..., description="Search query")):
    """
    Search across multiple manga sources (Mangapill, MangaDex, MangaSee, Mangakakalot).
    """
    from bs4 import BeautifulSoup
    import httpx

    q_clean = q.strip()
    results = []

    async def fetch_mangapill(client):
        url = f"https://mangapill.com/search?q={q_clean.replace(' ', '+')}"
        r = await client.get(url)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.select("a[href^='/manga/']"):
            title = a.text.strip()
            href = a.get("href")
            if href and title:
                results.append({
                    "title": title,
                    "url": f"https://mangapill.com{href}",
                    "source": "Mangapill"
                })

    async def fetch_mangasee(client):
        url = f"https://mangasee123.com/search/?name={q_clean.replace(' ', '+')}"
        r = await client.get(url)
        soup = BeautifulSoup(r.text, "html.parser")
        for div in soup.select("a.SeriesName"):
            title = div.text.strip()
            href = div.get("href")
            if href and title:
                results.append({
                    "title": title,
                    "url": f"https://mangasee123.com{href}",
                    "source": "MangaSee"
                })

    async def fetch_mangadex(client):
        url = f"https://api.mangadex.org/manga?limit=10&title={q_clean}"
        r = await client.get(url)
        data = r.json()
        for item in data.get("data", []):
            title = item["attributes"]["title"].get("en") or list(item["attributes"]["title"].values())[0]
            results.append({
                "title": title,
                "url": f"https://mangadex.org/title/{item['id']}",
                "source": "MangaDex"
            })

    async def fetch_mangakakalot(client):
        url = f"https://mangakakalot.com/search/story/{q_clean.replace(' ', '_')}"
        r = await client.get(url)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.select(".story_item a.item-img"):
            href = a.get("href")
            title_tag = a.find_next("h3")
            title = title_tag.text.strip() if title_tag else "Unknown"
            results.append({
                "title": title,
                "url": href,
                "source": "Mangakakalot"
            })

    async with httpx.AsyncClient(timeout=10) as client:
        await asyncio.gather(
            fetch_mangapill(client),
            fetch_mangadex(client),
            fetch_mangasee(client),
            fetch_mangakakalot(client)
        )

    return sorted(results, key=lambda r: r["source"])


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
