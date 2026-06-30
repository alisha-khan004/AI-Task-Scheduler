from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
import uuid


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SCHEDULED = "scheduled"


class TaskCategory(str, Enum):
    WORK = "work"
    PERSONAL = "personal"
    HEALTH = "health"
    FINANCE = "finance"
    LEARNING = "learning"
    OTHER = "other"


class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    priority: Priority = Priority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    category: TaskCategory = TaskCategory.OTHER
    due_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = []
    estimated_minutes: Optional[int] = None
    ai_suggestion: Optional[str] = None
    scheduled_time: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "status": self.status.value,
            "category": self.category.value,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "tags": self.tags,
            "estimated_minutes": self.estimated_minutes,
            "ai_suggestion": self.ai_suggestion,
            "scheduled_time": self.scheduled_time.isoformat() if self.scheduled_time else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: Priority = Priority.MEDIUM
    category: TaskCategory = TaskCategory.OTHER
    due_date: Optional[datetime] = None
    tags: List[str] = []
    estimated_minutes: Optional[int] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[Priority] = None
    status: Optional[TaskStatus] = None
    category: Optional[TaskCategory] = None
    due_date: Optional[datetime] = None
    tags: Optional[List[str]] = None
    estimated_minutes: Optional[int] = None


class AIScheduleRequest(BaseModel):
    task_ids: List[str]
    preferences: Optional[dict] = None


class AnalyticsResponse(BaseModel):
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    overdue_tasks: int
    completion_rate: float
    tasks_by_priority: dict
    tasks_by_category: dict
    avg_completion_time_minutes: Optional[float]
