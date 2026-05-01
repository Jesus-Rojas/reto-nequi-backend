from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import MessageAPIException
from app.schemas.message import ErrorDetail, ErrorResponse


async def message_api_exception_handler(
    request: Request, exc: MessageAPIException
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


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    details = "; ".join(
        f"Campo '{'->'.join(str(loc) for loc in e['loc'])}': {e['msg']}"
        for e in exc.errors()
    )
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            status="error",
            error=ErrorDetail(
                code="VALIDATION_ERROR",
                message="Error de validación en los datos enviados",
                details=details,
            ),
        ).model_dump(),
    )


async def internal_server_error_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            status="error",
            error=ErrorDetail(
                code="INTERNAL_SERVER_ERROR",
                message="Error interno del servidor",
                details=None,
            ),
        ).model_dump(),
    )
