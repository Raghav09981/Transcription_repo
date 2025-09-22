from fastapi import FastAPI, HTTPException, Request
from routes.transcription_routes import meeting_routes
from routes.calendar_routes import calendar_routes
from routes.whisper_routes import whisper_routes
from schemas.response_schema import BaseResponse
from constants.status_code_constants import status as status_code
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from routes.upload_file_routes import upload_file_routes
import os
from fastapi.middleware.cors import CORSMiddleware
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s - %(message)s')
app = FastAPI()

app.include_router(
    meeting_routes,
    prefix="/assistant/meetings",
    tags=["Meetings"]
)
app.include_router(upload_file_routes, prefix="/assistant/files", tags=["Uploads"])
app.include_router(whisper_routes, prefix="/assistant", tags=["Whisper Transcription"])
app.include_router(calendar_routes, prefix="/assistant", tags=["Calendar"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST, PUT, DELETE, OPTIONS, etc.
    allow_headers=["*"],  # Accept all headers
)

os.makedirs("uploads", exist_ok=True)
os.makedirs("static", exist_ok=True)


app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exceptions: RequestValidationError):
    errors = []
    for err in exceptions.errors():
        msg = err['msg']
        if msg.lower().startswith("value error,"):
            msg = msg[len("Value error, "):].strip()
        errors.append({
            'field': err['loc'][-1],
            'message': msg
        })
    return JSONResponse(
        status_code=status_code.HTTP_400_BAD_REQUEST,
        content=BaseResponse[None](
            data=None,
            message="Validation Failed",
            statusCode=status_code.HTTP_400_BAD_REQUEST
        ).dict() | {"errors": errors}
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exception: HTTPException):
    return JSONResponse(
        status_code=exception.status_code,
        content=BaseResponse[None](
            data=None,
            message=exception.detail,
            statusCode=exception.status_code
        ).dict()
    )
