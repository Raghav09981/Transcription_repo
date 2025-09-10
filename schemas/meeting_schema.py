from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from utils.validations import validate_meeting_name, validate_minutes


class MeetingSchema(BaseModel):
    title: Optional[str] = None
    meeting_date: Optional[str] = None
    meeting_time: Optional[str] = None
    meeting_duration: Optional[int] = None
    location: Optional[str] = None
    notes: Optional[str] = None


class MeetingCreate(MeetingSchema):
    pass


class MeetingResponse(MeetingSchema):
    id: str
    created_at: datetime = None
    updated_at: datetime = None
