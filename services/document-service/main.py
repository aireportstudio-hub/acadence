import os
import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app_env = os.environ.get("APP_ENV", "development")
    if app_env not in {"development", "staging", "production"}:
        raise ValueError("APP_ENV must be development, staging, or production")

    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise ValueError("LOG_LEVEL must be DEBUG, INFO, WARNING, ERROR, or CRITICAL")

    app.state.app_env = app_env
    app.state.log_level = log_level
    yield


app = FastAPI(title="Acadence Document Service", lifespan=lifespan)


@app.middleware("http")
async def request_correlation(request: Request, call_next):
    incoming_ids = request.headers.getlist("X-Request-ID")
    if len(incoming_ids) == 1 and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", incoming_ids[0]):
        request.state.request_id = incoming_ids[0]
    else:
        request.state.request_id = uuid4().hex

    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


def error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    response = JSONResponse(
        status_code=status_code,
        content={
            "code": code,
            "message": message,
            "request_id": request.state.request_id,
            "details": {},
        },
        headers=headers,
    )
    response.headers["X-Request-ID"] = request.state.request_id
    return response


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    codes = {
        401: "UNAUTHENTICATED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
    }
    return error_response(
        request,
        exc.status_code,
        codes.get(exc.status_code, f"HTTP_{exc.status_code}"),
        "Request could not be completed.",
        exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return error_response(request, 422, "VALIDATION_ERROR", "Request validation failed.")


@app.exception_handler(Exception)
async def unexpected_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return error_response(request, 500, "INTERNAL_SERVER_ERROR", "Internal server error.")


@app.get("/healthz")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
def readiness() -> dict[str, str]:
    return {"status": "ready"}
