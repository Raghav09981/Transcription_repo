from fastapi import APIRouter, HTTPException, UploadFile
import constants.status_code_constants as status_code
from repository.transcriprion_repo import (
    create_meeting,
    get_all_meetings,
    get_particular_meeting,
    delete_meeting,
    update_meeting
)

from schemas.meeting_schema import MeetingCreate, MeetingResponse
from schemas.response_schema import BaseResponse
from utils.validations import validate_id
from typing import List

router = APIRouter(prefix="/meetings", tags=MeetingCreate)


def create(file: UploadFile, meeting: MeetingCreate):
    new_meeting = create_meeting(
        meeting_data=meeting.dict(), audio_file=file)

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


def get_particular(meeting_id: str) -> BaseResponse[MeetingResponse]:
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
    return BaseResponse[MeetingResponse](
        data=MeetingResponse(**meeting),
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


def delete(meeting_id: str) -> BaseResponse[None]:
    if validate_id(meeting_id=meeting_id) is False:
        raise HTTPException(
            status_code=status_code.HTTP_BAD_REQUEST,
            detail="Invalid Id detected"
        )
    deleted = delete_meeting(meeting_id == meeting_id)
    if not deleted:
        raise HTTPException(
            status_code=status_code.HTTP_NOT_FOUND,
            detail="Meeting not found"
        )
    return BaseResponse[None](
        data=None,
        message="Meeting deleted successfully",
        statusCode=status_code.HTTP_OK
    )
