import os
import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from urllib.parse import urlparse
from uuid import UUID, uuid4

import httpx
import psycopg
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator
from starlette.exceptions import HTTPException as StarletteHTTPException

from projects import create_project, get_project, list_projects


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


app = FastAPI(title="Acadence Project Service", lifespan=lifespan)


@app.middleware("http")
async def request_correlation(request: Request, call_next):
    incoming_ids = request.headers.getlist("X-Request-ID")
    if len(incoming_ids) == 1 and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", incoming_ids[0]):
        request.state.request_id = incoming_ids[0]
    else:
        request.state.request_id = uuid4().hex

    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    if request.url.path.startswith("/v1/projects"):
        response.headers["Cache-Control"] = "no-store"
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
        503: "SERVICE_UNAVAILABLE",
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


class ProjectCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=10000)

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Title must not be blank")
        return value


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None


def verified_owner(request: Request) -> UUID:
    token = request.cookies.get("acadence_session")
    if not token or re.fullmatch(r"[A-Za-z0-9_-]{43}", token) is None:
        raise HTTPException(status_code=401)

    auth_url = os.environ.get("AUTH_SERVICE_URL", "")
    parsed = urlparse(auth_url)
    if (
        not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
        or (
            parsed.scheme != "https"
            and not (
                os.environ.get("APP_ENV", "development") == "development"
                and parsed.scheme == "http"
                and parsed.hostname in {"localhost", "127.0.0.1"}
            )
        )
    ):
        raise HTTPException(status_code=503)
    try:
        response = httpx.get(
            auth_url.rstrip("/") + "/v1/auth/session",
            headers={"Cookie": f"acadence_session={token}"},
            timeout=5.0,
            follow_redirects=False,
            trust_env=False,
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503) from exc
    if response.status_code == 401:
        raise HTTPException(status_code=401)
    if response.status_code != 200:
        raise HTTPException(status_code=503)
    try:
        data = response.json()
        user_id = data["user_id"]
        if not isinstance(user_id, str):
            raise ValueError("Invalid user ID")
        return UUID(user_id)
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=503) from exc


def creation_prerequisites() -> None:
    # Template snapshots and Billing eligibility must be implemented first.
    raise HTTPException(status_code=503)


def database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise HTTPException(status_code=503)
    return url


@app.get("/v1/projects", response_model=list[ProjectResponse])
def projects_index(owner: UUID = Depends(verified_owner)) -> list[ProjectResponse]:
    try:
        with psycopg.connect(database_url()) as connection:
            return [ProjectResponse.model_validate(p) for p in list_projects(connection, owner)]
    except psycopg.Error as exc:
        raise HTTPException(status_code=503) from exc


@app.get("/v1/projects/{project_id}", response_model=ProjectResponse)
def project_detail(project_id: UUID, owner: UUID = Depends(verified_owner)) -> ProjectResponse:
    try:
        with psycopg.connect(database_url()) as connection:
            project = get_project(connection, project_id, owner)
    except psycopg.Error as exc:
        raise HTTPException(status_code=503) from exc
    if project is None:
        raise HTTPException(status_code=404)
    return ProjectResponse.model_validate(project)


@app.post("/v1/projects", response_model=ProjectResponse, status_code=201)
def project_create(
    payload: ProjectCreate,
    request: Request,
    owner: UUID = Depends(verified_owner),
    _ready: None = Depends(creation_prerequisites),
) -> ProjectResponse:
    origin = os.environ.get("FRONTEND_APP_URL")
    if not origin or request.headers.get("origin") != origin:
        raise HTTPException(status_code=403)
    try:
        with psycopg.connect(database_url()) as connection:
            project = create_project(connection, owner, payload.title, payload.description)
    except psycopg.Error as exc:
        raise HTTPException(status_code=503) from exc
    return ProjectResponse.model_validate(project)