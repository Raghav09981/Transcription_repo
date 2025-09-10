from controllers import transcript_controllers
from schemas.meeting_schema import MeetingCreate, MeetingResponse
from schemas.response_schema import BaseResponse
from configs.router_config import create_router
from fastapi import UploadFile, Query, File, Form
from typing import List

meeting_routes = create_router(prefix="", tags=["Meetings"])


@meeting_routes.post("", response_model=BaseResponse[MeetingCreate])
def create_meeting_route(upload_file: UploadFile = File(...),
                         title: str = Form(None),
                         location: str = Form(None),
                         meeting_date: str = Form(None),
                         meeting_time: str = Form(None),
                         meeting_duration: int = Form(None)
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
def get_all_students_route(search: str = Query(None, description="Search for meeting")):
    return transcript_controllers.get_all(search=search)


@meeting_routes .get("/{meeting_id}", response_model=BaseResponse[MeetingResponse])
def get_student_route(meeting_id: str):
    return transcript_controllers.get_particular(meeting_id=meeting_id)


@meeting_routes.put("/{meeting_id}", response_model=BaseResponse[MeetingCreate])
def update_student_route(meeting_id: str, meeting: MeetingCreate):
    return transcript_controllers.update(meeting_id=meeting_id, meeting=meeting)


@meeting_routes.delete("/{meeting_id}", response_model=BaseResponse[None])
def delete_student_route(meeting_id: str):
    return transcript_controllers.delete(meeting_id=meeting_id)
