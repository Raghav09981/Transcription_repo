from controllers import calendar_controllers
from schemas.calendar_schema import CalendarEventCreate, CalendarEventUpdate, CalendarEventResponse
from schemas.response_schema import BaseResponse
from configs.router_config import create_router


calendar_routes = create_router(prefix="/calendar", tags=["Calendar"])


@calendar_routes.post("/events", response_model=BaseResponse[CalendarEventResponse])
def create_calendar_event_route(event_data: CalendarEventCreate):
    """
    Create a new Google Calendar event.
    
    Example request:
    ```json
    {
        "title": "Team Meeting",
        "description": "Weekly team sync",
        "start_time_iso": "2024-01-15T10:00:00Z",
        "duration_minutes": 60,
        "attendees": ["john@example.com", "jane@example.com"],
        "location": "Conference Room A"
    }
    ```
    """
    return calendar_controllers.create_event(event_data=event_data)


@calendar_routes.get("/events/{event_id}", response_model=BaseResponse[CalendarEventResponse])
def get_calendar_event_route(event_id: str):
    """
    Get a Google Calendar event by ID.
    
    Args:
        event_id: Google Calendar event ID
    """
    return calendar_controllers.get_event(event_id=event_id)


@calendar_routes.put("/events/{event_id}", response_model=BaseResponse[CalendarEventResponse])
def update_calendar_event_route(event_id: str, event_data: CalendarEventUpdate):
    """
    Update an existing Google Calendar event.
    
    Only provided fields will be updated. All fields are optional.
    
    Example request:
    ```json
    {
        "title": "Updated Team Meeting",
        "start_time_iso": "2024-01-15T11:00:00Z",
        "duration_minutes": 90,
        "attendees": ["john@example.com", "jane@example.com", "bob@example.com"]
    }
    ```
    
    Args:
        event_id: Google Calendar event ID
    """
    return calendar_controllers.update_event(event_id=event_id, event_data=event_data)


@calendar_routes.delete("/events/{event_id}", response_model=BaseResponse[None])
def delete_calendar_event_route(event_id: str):
    """
    Delete a Google Calendar event.
    
    Args:
        event_id: Google Calendar event ID
    """
    return calendar_controllers.delete_event(event_id=event_id)
