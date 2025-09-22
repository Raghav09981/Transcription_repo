from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CalendarEventCreate(BaseModel):
    title: str = Field(..., description="Event title")
    description: Optional[str] = Field(None, description="Event description")
    start_time_iso: str = Field(..., description="Start time in ISO format (e.g., '2024-01-01T10:00:00Z')")
    end_time_iso: Optional[str] = Field(None, description="End time in ISO format. If not provided, duration_minutes will be used")
    duration_minutes: Optional[int] = Field(30, description="Duration in minutes (used if end_time_iso not provided)")
    attendees: Optional[List[str]] = Field(default_factory=list, description="List of attendee email addresses")
    location: Optional[str] = Field(None, description="Event location")
    timezone: Optional[str] = Field("UTC", description="Timezone for the event")


class CalendarEventUpdate(BaseModel):
    title: Optional[str] = Field(None, description="Event title")
    description: Optional[str] = Field(None, description="Event description")
    start_time_iso: Optional[str] = Field(None, description="Start time in ISO format")
    end_time_iso: Optional[str] = Field(None, description="End time in ISO format")
    duration_minutes: Optional[int] = Field(None, description="Duration in minutes")
    attendees: Optional[List[str]] = Field(None, description="List of attendee email addresses")
    location: Optional[str] = Field(None, description="Event location")


class CalendarEventResponse(BaseModel):
    event_id: str = Field(..., description="Google Calendar event ID")
    title: str = Field(..., description="Event title")
    description: Optional[str] = Field(None, description="Event description")
    start_time_iso: str = Field(..., description="Start time in ISO format")
    end_time_iso: str = Field(..., description="End time in ISO format")
    attendees: List[str] = Field(default_factory=list, description="List of attendee email addresses")
    location: Optional[str] = Field(None, description="Event location")
    html_link: Optional[str] = Field(None, description="Google Calendar web link")
    hangout_link: Optional[str] = Field(None, description="Google Meet link")
    status: str = Field(..., description="Event status (confirmed, cancelled, etc.)")
    created_at: Optional[str] = Field(None, description="Event creation time")
    updated_at: Optional[str] = Field(None, description="Event last update time")
