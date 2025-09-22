from fastapi import HTTPException
import constants.status_code_constants as status_code
from services.calendar_service import (
    create_calendar_event,
    get_calendar_event,
    update_calendar_event,
    delete_calendar_event
)
from schemas.calendar_schema import CalendarEventCreate, CalendarEventUpdate, CalendarEventResponse
from schemas.response_schema import BaseResponse
from datetime import datetime, timedelta


def create_event(event_data: CalendarEventCreate) -> BaseResponse[CalendarEventResponse]:
    """Create a new calendar event"""
    try:
        # Calculate end_time_iso if not provided
        end_time_iso = event_data.end_time_iso
        if not end_time_iso and event_data.duration_minutes:
            start_dt = datetime.fromisoformat(event_data.start_time_iso.replace("Z", ""))
            end_dt = start_dt + timedelta(minutes=event_data.duration_minutes)
            end_time_iso = end_dt.isoformat() + "Z"

        event = create_calendar_event(
            title=event_data.title,
            description=event_data.description,
            start_time_iso=event_data.start_time_iso,
            duration_minutes=event_data.duration_minutes or 30,
            attendees=event_data.attendees or [],
            location=event_data.location,
            end_time_iso=end_time_iso
        )

        return BaseResponse[CalendarEventResponse](
            data=CalendarEventResponse(**event),
            message="Calendar event created successfully",
            statusCode=status_code.HTTP_CREATED
        )

    except Exception as e:
        raise HTTPException(
            status_code=status_code.HTTP_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create calendar event: {str(e)}"
        )


def get_event(event_id: str) -> BaseResponse[CalendarEventResponse]:
    """Get a calendar event by ID"""
    try:
        event = get_calendar_event(event_id)

        return BaseResponse[CalendarEventResponse](
            data=CalendarEventResponse(**event),
            message="Calendar event retrieved successfully",
            statusCode=status_code.HTTP_OK
        )

    except Exception as e:
        raise HTTPException(
            status_code=status_code.HTTP_NOT_FOUND,
            detail=f"Failed to get calendar event: {str(e)}"
        )


def update_event(event_id: str, event_data: CalendarEventUpdate) -> BaseResponse[CalendarEventResponse]:
    """Update an existing calendar event"""
    try:
        # Calculate end_time_iso if duration_minutes provided but end_time_iso not provided
        end_time_iso = event_data.end_time_iso
        if not end_time_iso and event_data.duration_minutes and event_data.start_time_iso:
            start_dt = datetime.fromisoformat(event_data.start_time_iso.replace("Z", ""))
            end_dt = start_dt + timedelta(minutes=event_data.duration_minutes)
            end_time_iso = end_dt.isoformat() + "Z"

        event = update_calendar_event(
            event_id=event_id,
            title=event_data.title,
            description=event_data.description,
            start_time_iso=event_data.start_time_iso,
            end_time_iso=end_time_iso,
            duration_minutes=event_data.duration_minutes,
            attendees=event_data.attendees,
            location=event_data.location
        )

        return BaseResponse[CalendarEventResponse](
            data=CalendarEventResponse(**event),
            message="Calendar event updated successfully",
            statusCode=status_code.HTTP_OK
        )

    except Exception as e:
        raise HTTPException(
            status_code=status_code.HTTP_BAD_REQUEST,
            detail=f"Failed to update calendar event: {str(e)}"
        )


def delete_event(event_id: str) -> BaseResponse[None]:
    """Delete a calendar event"""
    try:
        success = delete_calendar_event(event_id)

        if not success:
            raise HTTPException(
                status_code=status_code.HTTP_NOT_FOUND,
                detail="Calendar event not found"
            )

        return BaseResponse[None](
            data=None,
            message="Calendar event deleted successfully",
            statusCode=status_code.HTTP_OK
        )

    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status_code.HTTP_NOT_FOUND,
                detail="Calendar event not found"
            )
        else:
            raise HTTPException(
                status_code=status_code.HTTP_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete calendar event: {str(e)}"
            )
