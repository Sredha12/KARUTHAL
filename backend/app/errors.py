from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        detail_msg = exc.detail
        if isinstance(detail_msg, list):
            detail_msg = "; ".join(str(d) for d in detail_msg)
        elif not isinstance(detail_msg, str):
            detail_msg = str(detail_msg)

        return JSONResponse(
            status_code=exc.status_code,
            content={"message": detail_msg},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        # Never echo raw submitted passwords or descriptions
        field_errors = []
        for err in exc.errors():
            loc = " -> ".join(str(x) for x in err.get("loc", []) if x not in ("body",))
            msg = err.get("msg", "Invalid value")
            if loc:
                field_errors.append(f"{loc}: {msg}")
            else:
                field_errors.append(msg)

        summary = "; ".join(field_errors) if field_errors else "Validation failed for request data."
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"message": f"Invalid request data: {summary}"},
        )

    @app.exception_handler(SQLAlchemyError)
    async def database_exception_handler(request: Request, exc: SQLAlchemyError):
        # Protect internal database structure and return sanitized message
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"message": "Database service is temporarily unavailable. Please retry shortly."},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        # Do not expose internal traceback to client
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "An unexpected internal server error occurred."},
        )
