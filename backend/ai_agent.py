"""
AI Agent for intelligent task scheduling and suggestions.
Uses Claude AI to analyze tasks and provide smart scheduling recommendations.
"""

import os
import json
from typing import List, Optional
from datetime import datetime, timedelta
import anthropic

from models import Task, Priority, TaskStatus


class AITaskAgent:
    """
    AI-powered agent that analyzes tasks and generates intelligent scheduling
    recommendations, priority suggestions, and productivity insights.
    """

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        self.model = "claude-opus-4-6"

    def analyze_and_prioritize(self, tasks: List[Task]) -> List[dict]:
        """
        Analyze a list of tasks and return AI-generated priority suggestions
        with explanations for each task.
        """
        if not tasks:
            return []

        task_data = [
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "current_priority": t.priority.value,
                "category": t.category.value,
                "due_date": t.due_date.isoformat() if t.due_date else None,
                "estimated_minutes": t.estimated_minutes,
                "tags": t.tags,
            }
            for t in tasks
            if t.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED]
        ]

        prompt = f"""You are an expert productivity coach and task scheduler.
        
Analyze these tasks and provide intelligent scheduling recommendations:

{json.dumps(task_data, indent=2)}

Current time: {datetime.utcnow().isoformat()}

For each task, provide:
1. Recommended priority (low/medium/high/critical)
2. Suggested time slot (morning/afternoon/evening/flexible)
3. A brief, actionable suggestion (1-2 sentences max)
4. Estimated focus time if not provided

Return ONLY a JSON array with this exact structure:
[
  {{
    "id": "task_id",
    "recommended_priority": "high",
    "suggested_time": "morning",
    "suggestion": "Your actionable tip here.",
    "estimated_minutes": 30
  }}
]"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            text = response.content[0].text
            # Strip markdown fences if present
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            return json.loads(text.strip())
        except (json.JSONDecodeError, IndexError, KeyError):
            return []

    def generate_daily_schedule(self, tasks: List[Task], work_hours: dict = None) -> dict:
        """
        Generate an optimized daily schedule based on task priorities,
        estimated durations, and user work preferences.
        """
        if work_hours is None:
            work_hours = {"start": "09:00", "end": "18:00", "break": "13:00-14:00"}

        pending_tasks = [
            t for t in tasks if t.status in [TaskStatus.PENDING, TaskStatus.SCHEDULED]
        ]

        task_data = [t.to_dict() for t in pending_tasks[:20]]  # Limit for context

        prompt = f"""You are a master productivity scheduler.

Create an optimized daily schedule for today ({datetime.now().strftime('%A, %B %d, %Y')}).

Work hours: {json.dumps(work_hours)}
Tasks to schedule: {json.dumps(task_data, indent=2)}

Rules:
- Schedule high/critical priority tasks in peak morning hours
- Group similar category tasks together
- Include 5-min breaks between tasks over 45 minutes
- Respect due dates — overdue tasks get priority
- Don't schedule more than 6 hours of focused work

Return ONLY a JSON object:
{{
  "schedule": [
    {{
      "time": "09:00",
      "task_id": "id or null for breaks",
      "task_title": "Task name or Break",
      "duration_minutes": 30,
      "type": "task|break|buffer"
    }}
  ],
  "summary": "One sentence summary of the day.",
  "focus_score": 85,
  "tips": ["tip1", "tip2"]
}}"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            text = response.content[0].text
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            return json.loads(text.strip())
        except (json.JSONDecodeError, IndexError):
            return {"schedule": [], "summary": "Could not generate schedule.", "tips": []}

    def get_productivity_insights(self, tasks: List[Task]) -> dict:
        """
        Analyze completed and pending tasks to generate productivity insights
        and actionable improvement suggestions.
        """
        completed = [t for t in tasks if t.status == TaskStatus.COMPLETED]
        pending = [t for t in tasks if t.status == TaskStatus.PENDING]
        overdue = [
            t for t in tasks
            if t.due_date and t.due_date < datetime.utcnow()
            and t.status != TaskStatus.COMPLETED
        ]

        stats = {
            "total": len(tasks),
            "completed": len(completed),
            "pending": len(pending),
            "overdue": len(overdue),
            "completion_rate": round(len(completed) / len(tasks) * 100, 1) if tasks else 0,
            "categories": {},
            "priority_distribution": {},
        }

        for t in tasks:
            stats["categories"][t.category.value] = stats["categories"].get(t.category.value, 0) + 1
            stats["priority_distribution"][t.priority.value] = (
                stats["priority_distribution"].get(t.priority.value, 0) + 1
            )

        prompt = f"""You are a productivity analytics expert.

Analyze this task completion data and provide insights:
{json.dumps(stats, indent=2)}

Return ONLY a JSON object:
{{
  "headline_insight": "One powerful insight about their productivity.",
  "strengths": ["strength1", "strength2"],
  "improvement_areas": ["area1", "area2"],
  "weekly_goal": "One specific, measurable goal for this week.",
  "motivation_quote": "A relevant motivational quote."
}}"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            text = response.content[0].text
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            insights = json.loads(text.strip())
            insights["stats"] = stats
            return insights
        except (json.JSONDecodeError, IndexError):
            return {"stats": stats, "headline_insight": "Keep making progress!"}

    def suggest_task_breakdown(self, task: Task) -> List[dict]:
        """
        Break down a complex task into smaller, actionable subtasks.
        """
        prompt = f"""Break down this task into 3-6 concrete, actionable subtasks:

Task: {task.title}
Description: {task.description or 'No description'}
Estimated time: {task.estimated_minutes or 'Unknown'} minutes
Category: {task.category.value}

Return ONLY a JSON array:
[
  {{
    "title": "Subtask title",
    "description": "What exactly to do",
    "estimated_minutes": 15,
    "order": 1
  }}
]"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            text = response.content[0].text
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            return json.loads(text.strip())
        except (json.JSONDecodeError, IndexError):
            return []
