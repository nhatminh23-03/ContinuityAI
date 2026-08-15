"""Error envelope. Frozen by docs/API_CONTRACT.md section 9."""

from pydantic import BaseModel

from .enums import ErrorCode


class ErrorBody(BaseModel):
    code: ErrorCode
    message: str
    details: dict | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody
