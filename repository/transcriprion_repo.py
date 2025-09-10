from bson import ObjectId
from database.transcript_database import transcript_collection
from pymongo import ReturnDocument
from services.transcript_services import transcript_audio
from fastapi import UploadFile
from utils.file_utils import save_upload_file
from utils.validations import now

currentTime = now()


def create_meeting(meeting_data: dict, audio_file: UploadFile):
    saved_file_path = save_upload_file(
        upload_file=audio_file, destination=audio_file.filename)
    transcript_data = transcript_audio(audio_file_path=saved_file_path)
    meeting_data['updated_at'] = currentTime
    meeting_data['created_at'] = currentTime
    meeting_data['notes'] = transcript_data["transcription"]
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
                "_id": {"$toString": "$_id"},
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


def delete_meeting(meeting_id: str):
    result = transcript_collection.delete_one({"_id": ObjectId(meeting_id)})
    return result.deleted_count > 0
