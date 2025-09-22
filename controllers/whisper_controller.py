from fastapi import UploadFile, Request, HTTPException
from services.upload_service import save_audio_file
from services.whisper_service import transcribe_audio_with_whisper
from schemas.response_schema import BaseResponse
import constants.status_code_constants as status_code
import os


async def upload_and_transcribe_with_whisper(request: Request, file: UploadFile) -> BaseResponse[dict]:
    """Upload audio file with chunked upload and transcribe using Whisper model."""
    
    try:
        # Step 1: Save the uploaded file using existing chunked upload service
        relative_url = await save_audio_file(file)  # e.g., "/uploads/filename.ext"
        
        # Step 2: Get the actual file path for transcription
        if relative_url.startswith("/uploads/"):
            filename = relative_url.split("/uploads/", 1)[1]
            file_path = os.path.join("uploads", filename)
        else:
            raise HTTPException(
                status_code=status_code.HTTP_INTERNAL_SERVER_ERROR,
                detail="Invalid file path returned from upload"
            )
        
        # Step 3: Transcribe the uploaded file using Whisper
        transcription_result = transcribe_audio_with_whisper(file_path)
        
        # Step 4: Check for transcription errors
        if "error" in transcription_result:
            raise HTTPException(
                status_code=status_code.HTTP_INTERNAL_SERVER_ERROR,
                detail=f"Transcription failed: {transcription_result['error']}"
            )
        
        # Step 5: Build relative path for the uploaded file
        url = f"uploads/{filename}"
        
        # Step 6: Get file metadata
        content_type = getattr(file, "content_type", None)
        
        # Try to get size by seeking the underlying SpooledTemporaryFile if available
        size = None
        try:
            file_spool = file.file
            current_pos = file_spool.tell()
            file_spool.seek(0, 2)
            size = file_spool.tell()
            file_spool.seek(current_pos)
        except Exception:
            size = None
        
        # Step 7: Prepare response data
        response_data = {
            "upload_info": {
                "url": url,
                "name": file.filename,
                "size": size if size is not None else 0,
                "content_type": content_type,
                "file_path": file_path
            },
            "transcription": {
                "text": transcription_result["transcription"],
                "model_used": transcription_result["model_used"],
                "chunks_processed": transcription_result["chunks_processed"],
                "transcript_file_path": transcription_result["file_path"]
            }
        }
        
        return BaseResponse[dict](
            data=response_data,
            message="File uploaded and transcribed successfully with Whisper",
            statusCode=status_code.HTTP_CREATED
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        # Handle any other unexpected errors
        raise HTTPException(
            status_code=status_code.HTTP_INTERNAL_SERVER_ERROR,
            detail=f"Upload and transcription failed: {str(e)}"
        )


async def transcribe_existing_file_with_whisper(file_path: str) -> BaseResponse[dict]:
    """Transcribe an existing audio file using Whisper model."""
    
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status_code.HTTP_NOT_FOUND,
                detail=f"File not found: {file_path}"
            )
        
        # Transcribe the file using Whisper
        transcription_result = transcribe_audio_with_whisper(file_path)
        
        # Check for transcription errors
        if "error" in transcription_result:
            raise HTTPException(
                status_code=status_code.HTTP_INTERNAL_SERVER_ERROR,
                detail=f"Transcription failed: {transcription_result['error']}"
            )
        
        response_data = {
            "file_info": {
                "file_path": file_path,
                "filename": os.path.basename(file_path)
            },
            "transcription": {
                "text": transcription_result["transcription"],
                "model_used": transcription_result["model_used"],
                "chunks_processed": transcription_result["chunks_processed"],
                "transcript_file_path": transcription_result["file_path"]
            }
        }
        
        return BaseResponse[dict](
            data=response_data,
            message="File transcribed successfully with Whisper",
            statusCode=status_code.HTTP_OK
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        # Handle any other unexpected errors
        raise HTTPException(
            status_code=status_code.HTTP_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {str(e)}"
        )
