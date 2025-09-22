from fastapi import APIRouter, HTTPException
import constants.status_code_constants as status_code
from repository.transcriprion_repo import (
    create_meeting,
    get_all_meetings,
    get_particular_meeting,
    archive_meeting,
    update_meeting
)

from schemas.meeting_schema import MeetingCreate, MeetingResponse
from schemas.response_schema import BaseResponse
from utils.validations import validate_id
from typing import List

router = APIRouter(prefix="/meetings", tags=MeetingCreate)


def create(meeting: MeetingCreate):
    new_meeting = create_meeting(
        meeting_data=meeting.dict())

    if not new_meeting:
        raise HTTPException(
            status_code=status_code.HTTP_INTERNAL_SERVER_ERROR,
            detail="Failed to create meeting"
        )
    return BaseResponse[MeetingCreate](
        data=MeetingCreate(**new_meeting),
        message="New meeting created successfully",
        statusCode=status_code.HTTP_CREATED
    )


def get_all(search: str = None) -> BaseResponse[List[MeetingResponse]]:
    meetings = get_all_meetings(search=search)

    if not meetings:
        raise HTTPException(
            status_code=status_code.HTTP_NOT_FOUND,
            detail="No meeting data found"
        )

    return BaseResponse[List[MeetingResponse]](
        data=[MeetingResponse.model_validate(
            meet).model_dump() for meet in meetings],
        message="Data returned successfully",
        statusCode=status_code.HTTP_OK
    )


def get_particular(meeting_id: str) -> BaseResponse[list[MeetingResponse]]:
    if validate_id(meeting_id=meeting_id) is False:
        raise HTTPException(
            status_code=status_code.HTTP_BAD_REQUEST,
            detail="Invalid id"
        )
    meeting = get_particular_meeting(meeting_id=meeting_id)
    if not meeting:
        raise HTTPException(
            status_code=status_code.HTTP_NOT_FOUND,
            detail="No meeting detail not found"
        )
    return BaseResponse[list[MeetingResponse]](
        data=[MeetingResponse(**meeting)],
        message="Meeting returned successfully",
        statusCode=status_code.HTTP_OK
    )


def update(meeting_id: str, meeting: MeetingCreate) -> BaseResponse[MeetingCreate]:
    if validate_id(meeting_id=meeting_id) is False:
        raise HTTPException(
            status_code=status_code.HTTP_BAD_REQUEST,
            detail="Invalid ID"
        )
    updated = update_meeting(student_id=meeting_id,
                             update_meeting_data=meeting.dict())
    if not updated:
        raise HTTPException(
            status_code=status_code.HTTP_BAD_REQUEST,
            detail="Cannot update the meeting"
        )
    return BaseResponse[MeetingCreate](
        data=MeetingCreate(**updated),
        message="Meeting updated successfully",
        statusCode=status_code.HTTP_ACCEPTED
    )


def archive(meeting_id: str) -> BaseResponse[None]:
    if validate_id(meeting_id=meeting_id) is False:
        raise HTTPException(
            status_code=status_code.HTTP_BAD_REQUEST,
            detail="Invalid Id detected"
        )
    deleted = archive_meeting(meeting_id=meeting_id)
    if not deleted:
        raise HTTPException(
            status_code=status_code.HTTP_NOT_FOUND,
            detail="Meeting not found"
        )
    return BaseResponse[None](
        data=None,
        message="Meeting archived successfully",
        statusCode=status_code.HTTP_OK
    )


 


def set_participants(meeting_id: str, owner: str, attendees: list[str]) -> BaseResponse[MeetingResponse]:
    if validate_id(meeting_id=meeting_id) is False:
        raise HTTPException(
            status_code=status_code.HTTP_BAD_REQUEST,
            detail="Invalid Id detected"
        )
    from repository.transcriprion_repo import set_owner_and_attendees
    updated = set_owner_and_attendees(meeting_id=meeting_id, owner=owner, attendees=attendees)
    if not updated:
        raise HTTPException(
            status_code=status_code.HTTP_NOT_FOUND,
            detail="Meeting not found"
        )
    return BaseResponse[MeetingResponse](
        data=MeetingResponse(**updated),
        message="Participants updated successfully",
        statusCode=status_code.HTTP_OK
    )


def auto_schedule_meeting(meeting_id: str) -> BaseResponse[dict]:
    if validate_id(meeting_id=meeting_id) is False:
        raise HTTPException(
            status_code=status_code.HTTP_BAD_REQUEST,
            detail="Invalid Id detected"
        )
    from repository.transcriprion_repo import get_particular_meeting, update_meeting
    from services.ai_actions_service import analyze_for_meeting_action
    from services.calendar_service import create_calendar_event

    meeting = get_particular_meeting(meeting_id=meeting_id)
    if not meeting:
        raise HTTPException(status_code=status_code.HTTP_NOT_FOUND, detail="Meeting not found")

    analysis = analyze_for_meeting_action(notes=meeting.get("notes", ""))
    if not analysis.get("should_schedule"):
        return BaseResponse[dict](
            data=analysis,
            message="No meeting scheduling action detected",
            statusCode=status_code.HTTP_OK
        )

    # Collect participants
    attendees = meeting.get("attendees", []) or []
    owner = meeting.get("owner")
    if owner:
        attendees = list({owner, *attendees})

    event = create_calendar_event(
        title=analysis.get("title") or meeting.get("title") or "Follow-up Meeting",
        description=analysis.get("description") or "",
        start_time_iso=analysis.get("start_time_iso"),
        duration_minutes=analysis.get("duration_minutes", 30),
        attendees=attendees
    )

    # Persist event info on meeting
    updated = update_meeting(meeting_id=meeting_id, update_meeting_data={
        "calendar_event": event
    })

    return BaseResponse[dict](
        data={"analysis": analysis, "event": event},
        message="Auto-schedule completed",
        statusCode=status_code.HTTP_OK
    )