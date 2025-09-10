from datetime import datetime
from controllers import transcript_controllers
from schemas.meeting_schema import MeetingCreate, MeetingResponse
from schemas.response_schema import BaseResponse
from configs.router_config import create_router
from fastapi import UploadFile, Query, File, Form
from typing import List

meeting_routes = create_router(prefix="", tags=["Meetings"])


@meeting_routes.post("", response_model=BaseResponse[MeetingCreate])
def create_meeting_route(
    upload_file: UploadFile = File(...),
    title: str = Form("Untitled Meeting"),
    location: str = Form("Unknown Location"),
    meeting_date: str = Form(datetime.now().strftime("%Y-%m-%d")),
    meeting_time: str = Form(datetime.now().strftime("%H:%M:%S")),
    meeting_duration: int = Form(2)  # default 60 minutes
):
    meeting_data = MeetingCreate(
        title=title,
        location=location,
        meeting_date=meeting_date,
        meeting_time=meeting_time,
        meeting_duration=meeting_duration
    )
    return transcript_controllers.create(file=upload_file, meeting=meeting_data)


@meeting_routes.get("", response_model=BaseResponse[List[MeetingResponse]])
def get_all_meeting_route(search: str = Query(None, description="Search for meeting")):
    return transcript_controllers.get_all(search=search)


@meeting_routes .get("/{meeting_id}", response_model=BaseResponse[MeetingResponse])
def get_meeting_route(meeting_id: str):
    return transcript_controllers.get_particular(meeting_id=meeting_id)


@meeting_routes.put("/{meeting_id}", response_model=BaseResponse[MeetingCreate])
def update_meeting_route(meeting_id: str, meeting: MeetingCreate):
    return transcript_controllers.update(meeting_id=meeting_id, meeting=meeting)


@meeting_routes.delete("/{meeting_id}", response_model=BaseResponse[None])
def delete_meeting_route(meeting_id: str):
    return transcript_controllers.delete(meeting_id=meeting_id)
