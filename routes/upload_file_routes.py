from fastapi import UploadFile, File, Request
from controllers.upload_controller import upload_audio_controller
from schemas.response_schema import BaseResponse, UploadedFileResponse
from configs.router_config import create_router

upload_file_routes = create_router(prefix="", tags=["Uploads"])


@upload_file_routes.post("", response_model=BaseResponse[UploadedFileResponse])
async def upload_audio(request: Request, file: UploadFile = File(...)):
    return await upload_audio_controller(request, file)
