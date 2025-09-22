from fastapi import UploadFile, Request
from services.upload_service import save_audio_file
from schemas.response_schema import BaseResponse, UploadedFileResponse


async def upload_audio_controller(request: Request, file: UploadFile) -> BaseResponse[UploadedFileResponse]:
    relative_url = await save_audio_file(file)  # e.g., "/uploads/filename.ext"

    # Return relative path instead of full URL
    if relative_url.startswith("/uploads/"):
        filename = relative_url.split("/uploads/", 1)[1]
        url = f"/uploads/{filename}"  # Just relative path
    else:
        url = relative_url.lstrip("/")  # Remove leading slash if present

    # Some clients may not send content_type; default to None
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

    payload = UploadedFileResponse(
        url=url,
        name=file.filename,
        size=size if size is not None else 0,
        contentType=content_type
    )

    return BaseResponse[UploadedFileResponse](
        data=payload,
        message="File uploaded successfully",
        statusCode=201
    )
