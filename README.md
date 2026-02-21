# 🌙 Astas888 Manga v2

**Astas888 Manga** is a self-hosted, multi-source manga downloader and reader service.  
It automatically fetches, downloads, and organizes manga chapters — with a sleek web dashboard, smart limiter, and progress tracking.

---

## 🚀 Quick Launch

### 🐳 Using Docker Compose (recommended)

```bash
# 1. Clone the repo
git clone https://github.com/Astas888/astas888-manga.git
cd astas888-manga

# 2. Build and start
sudo docker compose up -d --build

# 3. Open in browser
http://<your-server-ip>:55
```

### ✅ Health check

```bash
curl http://localhost:55/health
```

Expected output:
```json
{"status":"ok"}
```

---

## 🧩 Manual Setup (Dev Mode)

```bash
# 1. Install system dependencies
sudo apt update && sudo apt install -y python3 python3-venv redis-server

# 2. Clone repo
git clone https://github.com/Astas888/astas888-manga.git
cd astas888-manga

# 3. Install Python deps
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Run server
cd frontend
uvicorn server:app --host 0.0.0.0 --port 55
```

Open [http://localhost:55](http://localhost:55)  
🎉 You’ll see the dashboard.

---

## ⚙️ Features

| Feature | Description |
|----------|--------------|
| 🧠 Smart Limiter | Adaptive per-source rate control to prevent bans |
| 📚 Multi-Source | Supports :contentReference[oaicite:0]{index=0} (more coming soon) |
| 🔁 Auto Retry | Smart queue retry with exponential backoff |
| 🧱 OPDS Support | For external readers like Tachiyomi / KOReader |
| 📊 Dashboard | Web UI with progress bars, cancel, and history |
| 💾 Configurable Storage | Choose your download folder |
| 📈 Auto Fetch | Background job scans for new chapters |

---

## 🧠 API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| `GET` | `/health` | Server health check |
| `GET` | `/api/v1/settings/source-status` | Per-source limiter & success stats |
| `POST` | `/api/v1/download` | Start new manga download (`{"url": "https://mangapill.com/manga/one-piece"}`) |
| `GET` | `/api/v1/progress/{job_id}` | Get live job progress |
| `GET` | `/api/v1/history` | List completed downloads |
| `POST` | `/api/v1/cancel/{job_id}` | Cancel a queued or running job |

---

## 💻 Frontend (UI)

The built-in Vue 3 dashboard is served automatically from `/frontend` and loads on `/`.  
It includes:

- Chapter progress bars  
- Cancel button per job  
- Download history list  
- Auto-refresh every 5 s  

![Dashboard preview](docs/screenshot.png) *(optional)*

---

## 🧰 Maintenance

| Action | Command |
|--------|----------|
| Stop app | `sudo docker compose down` |
| Restart app | `sudo docker compose restart` |
| View logs | `sudo docker compose logs -f` |
| Update code | `git pull && sudo docker compose up -d --build` |

---

## 🔒 Optional: NGINX + SSL

Use a reverse proxy for HTTPS access:

```bash
sudo apt install nginx certbot python3-certbot-nginx
```

Then proxy `http://localhost:55` → `https://manga.yourdomain.com`  
and run `sudo certbot --nginx` to obtain a free certificate from :contentReference[oaicite:1]{index=1}.

---

## 🧑‍💻 License

MIT © 2026 — Created by **Astas888**

---

### 💬 Need help?
If you encounter an issue:
```bash
sudo docker compose logs web
```
and paste the last 30 lines in a new issue on GitHub.
