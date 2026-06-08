"""Import all models for Alembic autogenerate."""

from app.db.base import Base
from app.modules.chat.models import ChatMessage, ChatSession
from app.modules.finance.models import FinanceCategory, FinanceGoal, FinanceTransaction
from app.modules.habits.models import Habit, HabitLog
from app.modules.memory.models import AIMemory, AINote, DailyJournal, EntityRelation, WeeklyReview
from app.modules.notes.models import Document, DocumentChunk, Note
from app.modules.reminders.models import Reminder
from app.modules.study.models import Flashcard, StudySession, StudySubject, StudyTopic
from app.modules.tasks.models import Task
from app.modules.users.models import User
from app.modules.workout.models import Exercise, PhysicalProfile, WorkoutPlan, WorkoutSession, WorkoutSet

__all__ = ["Base"]
