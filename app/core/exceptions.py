from starlette import status


class MessageAPIException(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        details: str | None = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ):
        self.code = code
        self.message = message
        self.details = details
        self.status_code = status_code
        super().__init__(message)


class InvalidFormatException(MessageAPIException):
    def __init__(self, details: str | None = None):
        super().__init__(
            code="INVALID_FORMAT",
            message="Formato de mensaje inválido",
            details=details,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


class DuplicateMessageException(MessageAPIException):
    def __init__(self, message_id: str):
        super().__init__(
            code="DUPLICATE_MESSAGE",
            message="El mensaje ya existe",
            details=f"Ya existe un mensaje con el ID '{message_id}'",
            status_code=status.HTTP_409_CONFLICT,
        )


class SessionNotFoundException(MessageAPIException):
    def __init__(self, session_id: str):
        super().__init__(
            code="SESSION_NOT_FOUND",
            message="Sesión no encontrada",
            details=f"No se encontraron mensajes para la sesión '{session_id}'",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class UnauthorizedException(MessageAPIException):
    def __init__(self):
        super().__init__(
            code="UNAUTHORIZED",
            message="No autorizado",
            details="API key inválida o no proporcionada",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
