from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette import status

from app.core.exceptions import MessageAPIException
from app.schemas.message import ErrorDetail, ErrorResponse


def message_api_exception_handler(
    _request: Request, exc: MessageAPIException
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            status="error",
            error=ErrorDetail(
                code=exc.code,
                message=exc.message,
                details=exc.details,
            ),
        ).model_dump(),
    )


def validation_exception_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    error_messages = []
    for error in exc.errors():
        field_path = [str(loc) for loc in error["loc"]]
        field = "->".join(field_path)
        message = error["msg"]
        error_messages.append(f"Campo '{field}': {message}")

    details = "; ".join(error_messages)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            status="error",
            error=ErrorDetail(
                code="VALIDATION_ERROR",
                message="Error de validación en los datos enviados",
                details=details,
            ),
        ).model_dump(),
    )


def internal_server_error_handler(
    _request: Request, _exc: Exception
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            status="error",
            error=ErrorDetail(
                code="INTERNAL_SERVER_ERROR",
                message="Error interno del servidor",
                details=None,
            ),
        ).model_dump(),
    )
