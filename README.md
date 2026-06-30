# TaskMind — AI-Powered Task Scheduler

> Intelligent task management driven by Claude AI. Prioritize smarter, schedule better, and get more done.

![TaskMind Dashboard](https://img.shields.io/badge/Status-Production%20Ready-00d9a3?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.11+-6c63ff?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-6c63ff?style=flat-square)
![React](https://img.shields.io/badge/React-18-6c63ff?style=flat-square)

---

## ✨ Features

- **AI Task Analysis** — Claude analyzes your tasks and suggests priority adjustments with reasoning
- **Smart Daily Planner** — AI-generated optimized schedules based on priority, deadlines & cognitive load
- **Task Breakdown** — Complex tasks decomposed into actionable subtasks automatically
- **Productivity Insights** — Pattern analysis with personalized improvement recommendations
- **Real-Time Notifications** — WebSocket-powered live updates and scheduler alerts
- **Auto-Escalation** — Tasks approaching deadlines get priority bumped automatically
- **Daily Digest** — Morning briefing of the day's workload at 8 AM

---

## 🏗 Architecture

```
taskmind/
├── backend/
│   ├── main.py          # FastAPI app — REST API + WebSocket endpoints
│   ├── models.py        # Pydantic data models (Task, Priority, Status…)
│   ├── ai_agent.py      # Claude AI integration — scheduling & analysis
│   ├── scheduler.py     # APScheduler — reminders, escalation, digest
│   └── requirements.txt
└── frontend/
    └── index.html       # React SPA — standalone, zero build step
```

---

## 🚀 Quick Start

### 1. Clone & Configure

```bash
git clone https://github.com/yourname/taskmind.git
cd taskmind
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env
```

### 2. Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API docs available at: `http://localhost:8000/docs`

### 3. Frontend

Open `frontend/index.html` directly in your browser — no build step required.

Or serve with any static server:
```bash
cd frontend
python -m http.server 3000
```

---

## 📡 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/tasks` | List all tasks (filterable) |
| `POST` | `/tasks` | Create a task |
| `PATCH` | `/tasks/{id}` | Update a task |
| `DELETE` | `/tasks/{id}` | Delete a task |
| `POST` | `/ai/analyze` | AI priority suggestions |
| `POST` | `/ai/schedule` | Generate daily schedule |
| `POST` | `/ai/breakdown/{id}` | Break task into subtasks |
| `GET` | `/ai/insights` | Productivity insights |
| `GET` | `/analytics` | Task statistics |
| `WS` | `/ws/notifications` | Real-time notifications |

---

## 🔑 Environment Variables

```env
ANTHROPIC_API_KEY=your_key_here
PORT=8000
```

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| AI | Anthropic Claude (claude-opus-4-6) |
| Backend | FastAPI + Python 3.11 |
| Scheduling | APScheduler |
| Frontend | React 18 (no build step) |
| Real-time | WebSockets |
| Data | In-memory (swap for PostgreSQL/Redis) |

---

## 📦 Production Notes

- Swap `task_store` dict for **PostgreSQL** + SQLAlchemy (or MongoDB)
- Add **Redis** for WebSocket pub/sub across multiple workers
- Deploy backend on **Railway / Fly.io / AWS ECS**
- Serve frontend on **Vercel / Netlify / CloudFront**
- Add rate limiting and auth (JWT recommended)

---

## 📄 License

MIT — build anything you want.
"# DeadlineAI-Smart-Productivity-Companion" 
