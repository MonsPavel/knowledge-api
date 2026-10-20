class AppError(Exception):
    error_type: str = "https://knowledge-api.dev/errors/server-error"
    title: str = "Internal Server Error"
    status: int = 500
    detail: str = "Произошла ошибка на сервере"

    def __init__(self, detail: str | None = None) -> None:
        if detail is not None:
            self.detail = detail

        super().__init__(self.detail)


class NotFoundError(AppError):
    error_type: str = "https://knowledge-api.dev/errors/not-found"
    title: str = "Not Found"
    status: int = 404
    detail: str = "Не найдено"

class ConflictError(AppError):
    error_type: str = "https://knowledge-api.dev/errors/conflict"
    title: str = "Conflict"
    status: int = 409
    detail: str = "Заметка с таким названием уже существует"

class RateLimitError(AppError):
    error_type: str = "https://knowledge-api.dev/errors/rate-limit"
    title: str = "Too Many Requests"
    status: int = 429
    detail: str = "Слишком много запросов"