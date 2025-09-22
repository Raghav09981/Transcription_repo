from bson import ObjectId
from database.transcript_database import transcript_collection
from pymongo import ReturnDocument
from services.transcript_services import transcript_audio
from utils.validations import now

currentTime = now()


def create_meeting(meeting_data: dict):
    audio_path = meeting_data.get("audio_recording_url")
    if audio_path:
        transcript_data = transcript_audio(
            audio_file_path=f".{audio_path}"
        )
        meeting_data['notes'] = transcript_data.get("transcription", "")
        print(transcript_data.get("file_path", ""))
        meeting_data['file_path'] = transcript_data.get(
            "file_path", "")
    result = transcript_collection.insert_one(meeting_data)
    meeting_data["id"] = str(result.inserted_id)
    return meeting_data


def get_all_meetings(search: str = None):
    pipeline = []

    if search:
        pipeline.append({
            "$match": {
                "$or": [
                    {"title": {"$regex": search, "$options": "i"}},
                    {"location": {"$regex": search, "$options": "i"}},
                ]
            }
        })

    pipeline.append({
        "$project": {
            "id": {"$toString": "$_id"},
            "title": 1,
            "meeting_date": 1,
            "meeting_duration": 1,
            "location": 1,
            "notes": 1,
            "audio_recording_url": 1,
            "file_path": 1,
            "owner": 1,
            "attendees": {"$ifNull": ["$attendees", []]},
            "attendee_count": {"$size": {"$ifNull": ["$attendees", []]}},
            "created_at": 1,
            "updated_at": 1,
            "is_archived": {"$ifNull": ["$is_archived", False]}
        }
    })

    return list(transcript_collection.aggregate(pipeline))


def get_particular_meeting(meeting_id: str):
    pipeline = [
        {"$match": {"_id": ObjectId(meeting_id)}},
        {
            "$project": {
                "id": {"$toString": "$_id"},
                "title": 1,
                "meeting_date": 1,
                "meeting_duration": 1,
                "location": 1,
                "notes": 1,
                "audio_recording_url": 1,
                "file_path": 1,
                "owner": 1,
                "attendees": {"$ifNull": ["$attendees", []]},
                "attendee_count": {"$size": {"$ifNull": ["$attendees", []]}},
                "created_at": 1,
                "updated_at": 1,
                "is_archived": {"$ifNull": ["$is_archived", False]}
            }
        }
    ]
    meeting = list(transcript_collection.aggregate(pipeline))
    return meeting[0] if meeting else None


def update_meeting(meeting_id: str, update_meeting_data: dict):
    update_meeting_data['updated_at'] = now()
    result = transcript_collection.find_one_and_update(
        {"_id": ObjectId(meeting_id)},
        {"$set": update_meeting_data},
        return_document=ReturnDocument.AFTER
    )
    if result:
        result["id"] = str(result["_id"])
        result.pop("_id", None)
    return result


def archive_meeting(meeting_id: str) -> bool:
    result = transcript_collection.update_one(
        {"_id": ObjectId(meeting_id)},
        {
            "$set": {
                "is_archived": True,
                "updated_at": currentTime
            }
        }
    )
    return result.modified_count > 0


 


def set_owner_and_attendees(meeting_id: str, owner: str, attendees: list[str]):
    attendees = [a for a in attendees if isinstance(a, str) and a.strip()]
    update_doc = {
        "$set": {
            "owner": owner,
            "updated_at": now()
        }
    }
    if attendees:
        update_doc["$set"]["attendees"] = attendees
    else:
        update_doc["$unset"] = {"attendees": ""}
    result = transcript_collection.find_one_and_update(
        {"_id": ObjectId(meeting_id)},
        update_doc,
        return_document=ReturnDocument.AFTER
    )
    if result:
        # Normalize id field for response models
        result["id"] = str(result["_id"]) if isinstance(result.get("_id"), ObjectId) else str(result.get("_id"))
        result.pop("_id", None)
    return result
