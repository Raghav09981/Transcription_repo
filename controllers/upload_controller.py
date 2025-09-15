from fastapi import UploadFile
from services.upload_service import save_audio_file
from schemas.response_schema import BaseResponse


async def upload_audio_controller(file: UploadFile) -> BaseResponse[str]:
    audio_url = await save_audio_file(file)
    return BaseResponse[str](
        data=audio_url,
        message="File uploaded successfully",
        statusCode=201
    )
