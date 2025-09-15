from fastapi import UploadFile, File
from controllers.upload_controller import upload_audio_controller
from schemas.response_schema import BaseResponse
from configs.router_config import create_router

upload_file_routes = create_router(prefix="", tags=["Uploads"])


@upload_file_routes.post("", response_model=BaseResponse[str])
async def upload_audio(file: UploadFile = File(...)):
    return await upload_audio_controller(file)
