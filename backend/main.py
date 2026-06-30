"""
AI Task Scheduler — FastAPI Backend
Endpoints for task CRUD, AI scheduling, analytics, and WebSocket notifications.
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from models import (
    Task, TaskCreate, TaskUpdate, TaskStatus,
    AIScheduleRequest, AnalyticsResponse, Priority
)
from ai_agent import AITaskAgent
from scheduler import TaskScheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory store (swap for PostgreSQL/MongoDB in production)
task_store: dict[str, Task] = {}
connected_clients: list[WebSocket] = []

ai_agent = AITaskAgent()
scheduler = TaskScheduler(task_store)


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.register_notification_callback(broadcast_notification)
    scheduler.start()
    logger.info("App started — scheduler running.")
    yield
    scheduler.stop()
    logger.info("App shutdown.")


app = FastAPI(
    title="AI Task Scheduler",
    description="Intelligent task management powered by Claude AI",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────── WebSocket ──────────────────────────────

async def broadcast_notification(payload: dict):
    """Broadcast a notification to all connected WebSocket clients."""
    message = json.dumps(payload)
    dead = []
    for ws in connected_clients:
        try:
            await ws.send_text(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        connected_clients.remove(ws)


@app.websocket("/ws/notifications")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep alive
    except WebSocketDisconnect:
        connected_clients.remove(websocket)


# ─────────────────────────── Tasks CRUD ─────────────────────────────

@app.get("/tasks", response_model=List[dict])
async def list_tasks(
    status: Optional[TaskStatus] = None,
    priority: Optional[Priority] = None,
    category: Optional[str] = None,
    search: Optional[str] = Query(None),
):
    tasks = list(task_store.values())

    if status:
        tasks = [t for t in tasks if t.status == status]
    if priority:
        tasks = [t for t in tasks if t.priority == priority]
    if category:
        tasks = [t for t in tasks if t.category.value == category]
    if search:
        q = search.lower()
        tasks = [t for t in tasks if q in t.title.lower() or (t.description and q in t.description.lower())]

    tasks.sort(key=lambda t: (
        {"critical": 0, "high": 1, "medium": 2, "low": 3}[t.priority.value],
        t.due_date or datetime.max,
    ))

    return [t.to_dict() for t in tasks]


@app.post("/tasks", response_model=dict, status_code=201)
async def create_task(data: TaskCreate):
    task = Task(**data.model_dump())
    task_store[task.id] = task

    if task.due_date:
        reminder_time = task.due_date.replace(hour=task.due_date.hour - 1) if task.due_date.hour > 0 else task.due_date
        scheduler.schedule_task_reminder(task, reminder_time)

    await broadcast_notification({
        "event": "task_created",
        "task_id": task.id,
        "message": f"New task created: '{task.title}'",
        "timestamp": datetime.utcnow().isoformat(),
    })

    return task.to_dict()


@app.get("/tasks/{task_id}", response_model=dict)
async def get_task(task_id: str):
    task = task_store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.to_dict()


@app.patch("/tasks/{task_id}", response_model=dict)
async def update_task(task_id: str, data: TaskUpdate):
    task = task_store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = data.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(task, key, value)

    if data.status == TaskStatus.COMPLETED:
        task.completed_at = datetime.utcnow()
        scheduler.cancel_reminder(task_id)

    task.updated_at = datetime.utcnow()

    await broadcast_notification({
        "event": "task_updated",
        "task_id": task_id,
        "message": f"Task '{task.title}' updated.",
        "timestamp": datetime.utcnow().isoformat(),
    })

    return task.to_dict()


@app.delete("/tasks/{task_id}", status_code=204)
async def delete_task(task_id: str):
    if task_id not in task_store:
        raise HTTPException(status_code=404, detail="Task not found")
    scheduler.cancel_reminder(task_id)
    del task_store[task_id]


# ─────────────────────────── AI Endpoints ───────────────────────────

@app.post("/ai/analyze", response_model=List[dict])
async def ai_analyze_tasks(body: AIScheduleRequest):
    """Get AI-powered priority and scheduling suggestions for selected tasks."""
    tasks = [task_store[tid] for tid in body.task_ids if tid in task_store]
    if not tasks:
        raise HTTPException(status_code=400, detail="No valid task IDs provided")
    suggestions = ai_agent.analyze_and_prioritize(tasks)
    return suggestions


@app.post("/ai/schedule", response_model=dict)
async def ai_generate_schedule():
    """Generate an optimized daily schedule using AI."""
    tasks = list(task_store.values())
    schedule = ai_agent.generate_daily_schedule(tasks)
    return schedule


@app.post("/ai/breakdown/{task_id}", response_model=List[dict])
async def ai_breakdown_task(task_id: str):
    """Use AI to break down a complex task into subtasks."""
    task = task_store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    subtasks = ai_agent.suggest_task_breakdown(task)
    return subtasks


@app.get("/ai/insights", response_model=dict)
async def ai_productivity_insights():
    """Get AI-generated productivity insights based on task history."""
    tasks = list(task_store.values())
    insights = ai_agent.get_productivity_insights(tasks)
    return insights


# ─────────────────────────── Analytics ──────────────────────────────

@app.get("/analytics", response_model=dict)
async def get_analytics():
    tasks = list(task_store.values())
    now = datetime.utcnow()

    completed = [t for t in tasks if t.status == TaskStatus.COMPLETED]
    pending = [t for t in tasks if t.status == TaskStatus.PENDING]
    overdue = [
        t for t in tasks
        if t.due_date and t.due_date < now and t.status != TaskStatus.COMPLETED
    ]

    completion_times = []
    for t in completed:
        if t.completed_at and t.created_at:
            delta = (t.completed_at - t.created_at).total_seconds() / 60
            completion_times.append(delta)

    by_priority = {}
    by_category = {}
    for t in tasks:
        by_priority[t.priority.value] = by_priority.get(t.priority.value, 0) + 1
        by_category[t.category.value] = by_category.get(t.category.value, 0) + 1

    return {
        "total_tasks": len(tasks),
        "completed_tasks": len(completed),
        "pending_tasks": len(pending),
        "overdue_tasks": len(overdue),
        "completion_rate": round(len(completed) / len(tasks) * 100, 1) if tasks else 0,
        "tasks_by_priority": by_priority,
        "tasks_by_category": by_category,
        "avg_completion_time_minutes": round(sum(completion_times) / len(completion_times), 1) if completion_times else None,
    }


@app.get("/scheduler/jobs", response_model=List[dict])
async def list_scheduled_jobs():
    return scheduler.get_scheduled_jobs()


@app.get("/health")
async def health():
    return {"status": "ok", "tasks": len(task_store), "timestamp": datetime.utcnow().isoformat()}
