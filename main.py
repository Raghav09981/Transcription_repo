from fastapi import FastAPI, HTTPException, Request
from routes.transcription_routes import meeting_routes
from schemas.response_schema import BaseResponse
from constants.status_code_constants import status as status_code
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


app = FastAPI()

app.include_router(
    meeting_routes,
    prefix="/meetings",
    tags=["Meetings"]
)


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
