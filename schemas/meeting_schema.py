from pydantic import BaseModel, field_validator, Field
from typing import Optional, Dict
from datetime import datetime
from utils.validations import validate_meeting_name, validate_minutes, validate_meeting_date


class MeetingSchema(BaseModel):
    title: Optional[str] = None
    meeting_date: Optional[int] = None
    meeting_duration: Optional[int] = None
    location: Optional[str] = None
    audio_recording_url: Optional[str] = None

    @field_validator("title")
    def validateTitle(cls, v):
        return validate_meeting_name(v)

    @field_validator("meeting_duration")
    def validateDuration(cls, v):
        return validate_minutes(v)

    @field_validator("meeting_date")
    def validateMeetingDate(cls, v):
        return validate_meeting_date(v)


class MeetingCreate(MeetingSchema):
    pass


class MeetingResponse(MeetingSchema):
    id: str
    notes: Optional[str] = None
    is_archived: bool = False
    file_path: Optional[str] = None
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
