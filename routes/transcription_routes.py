from controllers import transcript_controllers
from schemas.meeting_schema import MeetingCreate, MeetingResponse
from schemas.response_schema import BaseResponse
from configs.router_config import create_router
from fastapi import Query
from fastapi import Body
from typing import List

meeting_routes = create_router(prefix="", tags=["Meetings"])


@meeting_routes.post("", response_model=BaseResponse[MeetingCreate])
def create_meeting_route(meeting: MeetingCreate):
    return transcript_controllers.create(meeting=meeting)


@meeting_routes.get("", response_model=BaseResponse[List[MeetingResponse]])
def get_all_meeting_route(search: str = Query(None, description="Search for meeting")):
    return transcript_controllers.get_all(search=search)


@meeting_routes.get("/{meeting_id}", response_model=BaseResponse[list[MeetingResponse]])
def get_meeting_route(meeting_id: str):
    return transcript_controllers.get_particular(meeting_id=meeting_id)


@meeting_routes.put("/{meeting_id}", response_model=BaseResponse[MeetingCreate])
def update_meeting_route(meeting_id: str, meeting: MeetingCreate):
    return transcript_controllers.update(meeting_id=meeting_id, meeting=meeting)


@meeting_routes.patch("/{meeting_id}", response_model=BaseResponse[None])
def delete_meeting_route(meeting_id: str):
    return transcript_controllers.archive(meeting_id=meeting_id)


 


@meeting_routes.post("/{meeting_id}/participants", response_model=BaseResponse[MeetingResponse])
def set_participants_route(
    meeting_id: str,
    owner: str = Body(...),
    attendees: list[str] = Body(default_factory=list)
):
    return transcript_controllers.set_participants(meeting_id=meeting_id, owner=owner, attendees=attendees)


@meeting_routes.post("/{meeting_id}/auto-schedule", response_model=BaseResponse[dict])
def auto_schedule_meeting_route(meeting_id: str):
    return transcript_controllers.auto_schedule_meeting(meeting_id=meeting_id)
