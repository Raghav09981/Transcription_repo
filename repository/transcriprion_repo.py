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
            audio_file_path=f".{audio_path}")
        meeting_data['notes'] = transcript_data.get("transcription", "")

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
            "meeting_time": 1,
            "meeting_duration": 1,
            "location": 1,
            "notes": 1,
            "created_at": 1,
            "updated_at": 1
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
                "meeting_time": 1,
                "meeting_duration": 1,
                "location": 1,
                "notes": 1,
                "created_at": 1,
                "updated_at": 1
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
        result["_id"] = str(result["_id"])
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
