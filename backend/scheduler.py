"""
Task Scheduler — manages scheduling logic, reminders, and recurring tasks.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

from models import Task, TaskStatus, Priority

logger = logging.getLogger(__name__)


class TaskScheduler:
    """
    Manages all scheduling operations including:
    - Deadline reminders
    - Auto-escalation of overdue tasks
    - Daily digest generation
    - Background AI analysis runs
    """

    def __init__(self, task_store: dict):
        self.scheduler = AsyncIOScheduler()
        self.task_store = task_store  # Reference to shared in-memory store
        self.notification_callbacks = []

    def start(self):
        """Start the background scheduler."""
        # Check for overdue tasks every 15 minutes
        self.scheduler.add_job(
            self._check_overdue_tasks,
            "interval",
            minutes=15,
            id="overdue_check",
            replace_existing=True,
        )

        # Send daily digest at 8 AM
        self.scheduler.add_job(
            self._send_daily_digest,
            CronTrigger(hour=8, minute=0),
            id="daily_digest",
            replace_existing=True,
        )

        # Auto-escalate tasks approaching deadlines every hour
        self.scheduler.add_job(
            self._escalate_urgent_tasks,
            "interval",
            hours=1,
            id="escalation",
            replace_existing=True,
        )

        self.scheduler.start()
        logger.info("Task scheduler started.")

    def stop(self):
        """Gracefully stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Task scheduler stopped.")

    def schedule_task_reminder(self, task: Task, remind_at: datetime):
        """Schedule a one-time reminder for a specific task."""
        if remind_at <= datetime.utcnow():
            logger.warning(f"Reminder time {remind_at} is in the past for task {task.id}")
            return

        self.scheduler.add_job(
            self._send_reminder,
            DateTrigger(run_date=remind_at),
            args=[task.id],
            id=f"reminder_{task.id}",
            replace_existing=True,
        )
        logger.info(f"Reminder scheduled for task '{task.title}' at {remind_at}")

    def cancel_reminder(self, task_id: str):
        """Cancel a previously scheduled reminder."""
        job_id = f"reminder_{task_id}"
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            logger.info(f"Reminder cancelled for task {task_id}")

    def register_notification_callback(self, callback):
        """Register a callback function for notifications."""
        self.notification_callbacks.append(callback)

    async def _check_overdue_tasks(self):
        """Mark tasks as overdue and notify."""
        now = datetime.utcnow()
        overdue_count = 0

        for task_id, task in self.task_store.items():
            if (
                task.due_date
                and task.due_date < now
                and task.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED]
            ):
                overdue_count += 1
                await self._notify(
                    event="task_overdue",
                    task_id=task_id,
                    message=f"Task '{task.title}' is overdue!",
                )

        if overdue_count:
            logger.info(f"Found {overdue_count} overdue tasks.")

    async def _escalate_urgent_tasks(self):
        """Escalate priority of tasks due within 2 hours to CRITICAL."""
        now = datetime.utcnow()
        threshold = now + timedelta(hours=2)

        for task_id, task in self.task_store.items():
            if (
                task.due_date
                and now < task.due_date <= threshold
                and task.priority != Priority.CRITICAL
                and task.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED]
            ):
                task.priority = Priority.CRITICAL
                task.updated_at = now
                logger.info(f"Escalated task '{task.title}' to CRITICAL priority.")
                await self._notify(
                    event="priority_escalated",
                    task_id=task_id,
                    message=f"'{task.title}' escalated to CRITICAL — due in under 2 hours!",
                )

    async def _send_daily_digest(self):
        """Generate and send the daily task digest."""
        pending = [
            t for t in self.task_store.values()
            if t.status in [TaskStatus.PENDING, TaskStatus.SCHEDULED]
        ]
        due_today = [
            t for t in pending
            if t.due_date and t.due_date.date() == datetime.utcnow().date()
        ]

        await self._notify(
            event="daily_digest",
            task_id=None,
            message=f"Good morning! You have {len(pending)} pending tasks, "
                    f"{len(due_today)} due today.",
        )

    async def _send_reminder(self, task_id: str):
        """Send a reminder notification for a task."""
        task = self.task_store.get(task_id)
        if task and task.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            await self._notify(
                event="reminder",
                task_id=task_id,
                message=f"Reminder: '{task.title}' needs your attention!",
            )

    async def _notify(self, event: str, task_id: Optional[str], message: str):
        """Dispatch notification to all registered callbacks."""
        payload = {
            "event": event,
            "task_id": task_id,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        }
        for callback in self.notification_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(payload)
                else:
                    callback(payload)
            except Exception as e:
                logger.error(f"Notification callback error: {e}")

    def get_scheduled_jobs(self) -> List[Dict]:
        """Return info about all currently scheduled jobs."""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger),
            })
        return jobs
