"""Data model and JSON persistence for reminders."""
from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Enums & defaults
# ---------------------------------------------------------------------------

class Repeat(str, Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"

    @property
    def label(self) -> str:
        return {
            Repeat.NONE: "Doesn't repeat",
            Repeat.DAILY: "Every day",
            Repeat.WEEKLY: "Every week",
            Repeat.MONTHLY: "Every month",
            Repeat.YEARLY: "Every year",
        }[self]


DEFAULT_CATEGORIES = [
    {"id": "cat-personal", "name": "Personal", "color": "#4B8BF5"},
    {"id": "cat-work",     "name": "Work",     "color": "#2FB673"},
    {"id": "cat-shopping", "name": "Shopping", "color": "#F5883C"},
]


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class Category:
    id: str
    name: str
    color: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Category":
        return cls(id=d["id"], name=d["name"], color=d["color"])


@dataclass
class Reminder:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    note: str = ""
    due: Optional[str] = None            # ISO 8601 datetime or None
    repeat: str = Repeat.NONE.value
    important: bool = False
    done: bool = False
    category_id: Optional[str] = None
    created: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    completed_at: Optional[str] = None
    notified: bool = False               # true once due-time notification has fired

    # -- parsing helpers ---------------------------------------------------

    @property
    def due_dt(self) -> Optional[datetime]:
        if not self.due:
            return None
        try:
            return datetime.fromisoformat(self.due)
        except ValueError:
            return None

    @due_dt.setter
    def due_dt(self, value: Optional[datetime]) -> None:
        self.due = value.isoformat(timespec="minutes") if value else None

    # -- serialization -----------------------------------------------------

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Reminder":
        return cls(
            id=d.get("id") or str(uuid.uuid4()),
            title=d.get("title", ""),
            note=d.get("note", ""),
            due=d.get("due"),
            repeat=d.get("repeat", Repeat.NONE.value),
            important=bool(d.get("important", False)),
            done=bool(d.get("done", False)),
            category_id=d.get("category_id"),
            created=d.get("created") or datetime.now().isoformat(timespec="seconds"),
            completed_at=d.get("completed_at"),
            notified=bool(d.get("notified", False)),
        )

    # -- convenience -------------------------------------------------------

    def format_due(self) -> str:
        """Human-friendly due label (e.g. 'Today · 15:30', 'Tomorrow', 'Mon, 12 Feb')."""
        dt = self.due_dt
        if not dt:
            return ""
        today = date.today()
        d = dt.date()
        time_str = dt.strftime("%H:%M") if (dt.hour or dt.minute) else ""
        if d == today:
            day_str = "Today"
        elif d == today + timedelta(days=1):
            day_str = "Tomorrow"
        elif d == today - timedelta(days=1):
            day_str = "Yesterday"
        elif 0 < (d - today).days < 7:
            day_str = dt.strftime("%A")             # e.g. Friday
        else:
            day_str = dt.strftime("%a, %d %b")      # Fri, 14 Mar
            if d.year != today.year:
                day_str += dt.strftime(" %Y")
        return f"{day_str} · {time_str}" if time_str else day_str

    def is_overdue(self) -> bool:
        dt = self.due_dt
        return bool(dt and not self.done and dt < datetime.now())

    def advance_repeat(self) -> bool:
        """Roll due date forward one interval. Returns True if advanced."""
        dt = self.due_dt
        if not dt or self.repeat == Repeat.NONE.value:
            return False
        r = Repeat(self.repeat)
        if r == Repeat.DAILY:
            dt += timedelta(days=1)
        elif r == Repeat.WEEKLY:
            dt += timedelta(weeks=1)
        elif r == Repeat.MONTHLY:
            month = dt.month + 1
            year = dt.year + (1 if month > 12 else 0)
            month = ((month - 1) % 12) + 1
            try:
                dt = dt.replace(year=year, month=month)
            except ValueError:                       # e.g. Jan 31 -> Feb
                dt = dt.replace(year=year, month=month, day=28)
        elif r == Repeat.YEARLY:
            try:
                dt = dt.replace(year=dt.year + 1)
            except ValueError:                       # Feb 29
                dt = dt.replace(year=dt.year + 1, day=28)
        self.due_dt = dt
        self.notified = False
        return True


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

def data_dir() -> Path:
    base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    p = Path(base) / "reminder-app"
    p.mkdir(parents=True, exist_ok=True)
    return p


def data_file() -> Path:
    return data_dir() / "reminders.json"


class Store:
    """Loads and saves reminders + categories to a JSON file."""

    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = path or data_file()
        self.reminders: list[Reminder] = []
        self.categories: list[Category] = []
        self.load()

    # -- io ----------------------------------------------------------------

    def load(self) -> None:
        if not self.path.exists():
            self.categories = [Category.from_dict(c) for c in DEFAULT_CATEGORIES]
            self.reminders = []
            self.save()
            return
        try:
            raw = json.loads(self.path.read_text("utf-8"))
        except (json.JSONDecodeError, OSError):
            raw = {}
        self.categories = [Category.from_dict(c) for c in raw.get("categories", DEFAULT_CATEGORIES)]
        if not self.categories:
            self.categories = [Category.from_dict(c) for c in DEFAULT_CATEGORIES]
        self.reminders = [Reminder.from_dict(r) for r in raw.get("reminders", [])]

    def save(self) -> None:
        payload = {
            "categories": [c.to_dict() for c in self.categories],
            "reminders":  [r.to_dict() for r in self.reminders],
        }
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), "utf-8")
        tmp.replace(self.path)

    # -- reminder ops ------------------------------------------------------

    def add(self, reminder: Reminder) -> None:
        self.reminders.append(reminder)
        self.save()

    def update(self, reminder: Reminder) -> None:
        for i, r in enumerate(self.reminders):
            if r.id == reminder.id:
                self.reminders[i] = reminder
                break
        self.save()

    def delete(self, reminder_id: str) -> None:
        self.reminders = [r for r in self.reminders if r.id != reminder_id]
        self.save()

    def get(self, reminder_id: str) -> Optional[Reminder]:
        return next((r for r in self.reminders if r.id == reminder_id), None)

    def toggle_done(self, reminder_id: str) -> None:
        r = self.get(reminder_id)
        if not r:
            return
        if not r.done:
            # completing
            if r.repeat != Repeat.NONE.value and r.advance_repeat():
                # keep as active, just move due date forward
                pass
            else:
                r.done = True
                r.completed_at = datetime.now().isoformat(timespec="seconds")
        else:
            r.done = False
            r.completed_at = None
        self.save()

    # -- category ops ------------------------------------------------------

    def add_category(self, name: str, color: str) -> Category:
        c = Category(id=f"cat-{uuid.uuid4().hex[:8]}", name=name.strip(), color=color)
        self.categories.append(c)
        self.save()
        return c

    def delete_category(self, category_id: str) -> None:
        self.categories = [c for c in self.categories if c.id != category_id]
        for r in self.reminders:
            if r.category_id == category_id:
                r.category_id = None
        self.save()

    def category(self, category_id: Optional[str]) -> Optional[Category]:
        if not category_id:
            return None
        return next((c for c in self.categories if c.id == category_id), None)
