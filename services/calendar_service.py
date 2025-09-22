from datetime import datetime, timedelta
import os
from typing import List
import pickle

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = [
    "https://www.googleapis.com/auth/calendar"
]


def _get_calendar_service():
    credentials_path = os.getenv("GOOGLE_OAUTH_CREDENTIALS_FILE", "client_secret_1019005830189-pmjdbmhte1ueqp7j07rqhq2qfn2jkpr5.apps.googleusercontent.com.json")
    calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "primary")  # Default to primary calendar
    token_file = "token.pickle"
    
    creds = None
    # Load existing token if it exists
    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(credentials_path):
                raise RuntimeError(f"OAuth credentials file not found: {credentials_path}")
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            # Use port 8001 to match the redirect URI you configured
            creds = flow.run_local_server(port=8001, host='localhost')
        
        # Save the credentials for the next run
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)
    
    service = build("calendar", "v3", credentials=creds)
    return service, calendar_id


def create_calendar_event(title: str, description: str, start_time_iso: str, duration_minutes: int, attendees: List[str], location: str = None, end_time_iso: str = None) -> dict:
    """Create a new calendar event"""
    if not start_time_iso:
        start_time_iso = datetime.utcnow().isoformat() + "Z"
    
    # Use provided end_time_iso or calculate from duration
    if not end_time_iso:
        end_time_iso = (datetime.fromisoformat(start_time_iso.replace("Z", "")) + timedelta(minutes=duration_minutes)).isoformat() + "Z"

    service, calendar_id = _get_calendar_service()

    event_body = {
        "summary": title,
        "description": description or "",
        "start": {"dateTime": start_time_iso},
        "end": {"dateTime": end_time_iso},
        "attendees": [{"email": e} for e in (attendees or [])],
        "conferenceData": {
            "createRequest": {"requestId": f"req-{int(datetime.utcnow().timestamp())}"}
        },
        "guestsCanInviteOthers": True,
        "guestsCanModify": False,
        "sendUpdates": "all"
    }
    
    if location:
        event_body["location"] = location

    event = service.events().insert(calendarId=calendar_id, body=event_body, sendUpdates="all", conferenceDataVersion=1).execute()

    return _format_event_response(event)


def get_calendar_event(event_id: str) -> dict:
    """Get a calendar event by ID"""
    service, calendar_id = _get_calendar_service()
    
    try:
        event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
        return _format_event_response(event)
    except Exception as e:
        raise RuntimeError(f"Failed to get event {event_id}: {str(e)}")


def update_calendar_event(event_id: str, title: str = None, description: str = None, 
                         start_time_iso: str = None, end_time_iso: str = None, 
                         duration_minutes: int = None, attendees: List[str] = None, 
                         location: str = None) -> dict:
    """Update an existing calendar event"""
    service, calendar_id = _get_calendar_service()
    
    try:
        # Get existing event first
        existing_event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
        
        # Update only provided fields
        if title is not None:
            existing_event["summary"] = title
        if description is not None:
            existing_event["description"] = description
        if location is not None:
            existing_event["location"] = location
        if attendees is not None:
            existing_event["attendees"] = [{"email": e} for e in attendees]
        
        # Handle time updates
        if start_time_iso is not None:
            existing_event["start"] = {"dateTime": start_time_iso}
            
            # If end_time_iso not provided but duration_minutes is, calculate end time
            if end_time_iso is None and duration_minutes is not None:
                end_time_iso = (datetime.fromisoformat(start_time_iso.replace("Z", "")) + 
                              timedelta(minutes=duration_minutes)).isoformat() + "Z"
            
        if end_time_iso is not None:
            existing_event["end"] = {"dateTime": end_time_iso}
        
        # Update the event
        updated_event = service.events().update(
            calendarId=calendar_id, 
            eventId=event_id, 
            body=existing_event,
            sendUpdates="all"
        ).execute()
        
        return _format_event_response(updated_event)
        
    except Exception as e:
        raise RuntimeError(f"Failed to update event {event_id}: {str(e)}")


def delete_calendar_event(event_id: str) -> bool:
    """Delete a calendar event"""
    service, calendar_id = _get_calendar_service()
    
    try:
        service.events().delete(calendarId=calendar_id, eventId=event_id, sendUpdates="all").execute()
        return True
    except Exception as e:
        raise RuntimeError(f"Failed to delete event {event_id}: {str(e)}")


def _format_event_response(event: dict) -> dict:
    """Format Google Calendar event response for our API"""
    start_time = event.get("start", {}).get("dateTime", "")
    end_time = event.get("end", {}).get("dateTime", "")
    attendees = [a.get("email", "") for a in event.get("attendees", [])]
    
    return {
        "event_id": event.get("id"),
        "title": event.get("summary", ""),
        "description": event.get("description", ""),
        "start_time_iso": start_time,
        "end_time_iso": end_time,
        "attendees": attendees,
        "location": event.get("location", ""),
        "html_link": event.get("htmlLink", ""),
        "hangout_link": event.get("hangoutLink", ""),
        "status": event.get("status", ""),
        "created_at": event.get("created", ""),
        "updated_at": event.get("updated", "")
    }


