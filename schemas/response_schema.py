from typing import Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    data: Optional[T] = None
    message: str
    statusCode: int


class UploadedFileResponse(BaseModel):
    url: str
    name: str
    size: int
    contentType: Optional[str] = None