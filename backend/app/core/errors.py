"""Domain exceptions and their translation to the frozen error envelope.

docs/API_CONTRACT.md section 9. The frontend switches on error.code, never on message.
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.schemas.enums import ErrorCode

HTTP_STATUS: dict[ErrorCode, int] = {
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.VALIDATION_ERROR: 422,
    ErrorCode.UNAUTHORIZED: 401,
    ErrorCode.INSUFFICIENT_EVIDENCE: 409,
    ErrorCode.AI_EXTRACTION_FAILED: 502,
    ErrorCode.GRAPH_INCONSISTENCY: 500,
    ErrorCode.SIMULATION_FAILED: 500,
    ErrorCode.MITIGATION_GENERATION_FAILED: 500,
    ErrorCode.INTERNAL_ERROR: 500,
}


class DomainError(Exception):
    code: ErrorCode = ErrorCode.INTERNAL_ERROR

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class NotFoundError(DomainError):
    code = ErrorCode.NOT_FOUND


class ValidationError(DomainError):
    code = ErrorCode.VALIDATION_ERROR


class InsufficientEvidenceError(DomainError):
    code = ErrorCode.INSUFFICIENT_EVIDENCE


class GraphConsistencyError(DomainError):
    code = ErrorCode.GRAPH_INCONSISTENCY


class SimulationError(DomainError):
    code = ErrorCode.SIMULATION_FAILED


class AIExtractionError(DomainError):
    code = ErrorCode.AI_EXTRACTION_FAILED


class MitigationGenerationError(DomainError):
    code = ErrorCode.MITIGATION_GENERATION_FAILED


def envelope(code: ErrorCode, message: str, details: dict | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=HTTP_STATUS[code],
        content={"error": {"code": code.value, "message": message, "details": details or {}}},
    )


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def _domain(_: Request, exc: DomainError) -> JSONResponse:
        return envelope(exc.code, exc.message, exc.details)

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        return envelope(
            ErrorCode.VALIDATION_ERROR,
            "Request failed validation.",
            {"errors": str(exc.errors())},
        )


class NarrativeUnavailableError(AIExtractionError):
    """A provider could not produce a narrative and was told not to substitute the template.

    Exists so a chain of providers can tell "the model answered" from "this provider quietly fell back",
    which it otherwise cannot: both model providers degrade to the deterministic template internally, so
    a failed generation returns successfully and the next provider in the chain is never tried.

    That was a real bug rather than a hypothetical. With `AI_PROVIDER=hybrid` configured and the watsonx
    quota spent, `POST /simulations` returned template prose: watsonx caught its own HTTP 403, returned
    the template, and the chain saw a success and never reached OpenRouter — which was working. The
    chain's headline behaviour was dead code for all three narratives.

    So a provider inside a chain is constructed with `degrade_to_template = False` and raises this
    instead. The chain applies the template itself, once, after every model has actually been tried.
    """
