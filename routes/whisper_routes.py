from fastapi import UploadFile, File, Request, Query
from controllers.whisper_controller import upload_and_transcribe_with_whisper, transcribe_existing_file_with_whisper
from schemas.response_schema import BaseResponse
from configs.router_config import create_router

whisper_routes = create_router(prefix="/whisper", tags=["Whisper Transcription"])


@whisper_routes.post("/upload", response_model=BaseResponse[dict])
async def upload_and_transcribe_audio(request: Request, file: UploadFile = File(...)):
    """Upload audio file and transcribe it using Whisper model."""
    return await upload_and_transcribe_with_whisper(request, file)


@whisper_routes.post("/transcribe", response_model=BaseResponse[dict])
async def transcribe_existing_audio(file_path: str = Query(..., description="Path to the audio file to transcribe")):
    """Transcribe an existing audio file using Whisper model."""
    return await transcribe_existing_file_with_whisper(file_path)
