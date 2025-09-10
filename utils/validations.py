from datetime import datetime
from bson import ObjectId


def now() -> datetime:
    return datetime.now()


def validate_meeting_name(title: str) -> str:
    if not title or not title.strip():
        raise ValueError("Name cannot be empty.")

    stripped_title = title.strip()

    if len(stripped_title) < 3:
        raise ValueError("Name must be at least 3 characters long.")

    if len(stripped_title) > 25:
        raise ValueError("Name cannot exceed 25 characters.")

    if not stripped_title.replace(" ", "").isalpha():
        raise ValueError("Name can only contain letters and spaces.")

    return stripped_title


def validate_minutes(minutes: int) -> int:
    if minutes < 1:
        raise ValueError("Minutes must be greater than 1")
    return minutes


def validate_id(meeting_id: str) -> bool:
    return ObjectId.is_valid(meeting_id)
