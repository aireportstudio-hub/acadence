"""Exercise a minimal FastAPI route on the selected Python runtime."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel


class Health(BaseModel):
    status: str


app = FastAPI()


@app.get("/healthz", response_model=Health)
def health() -> Health:
    return Health(status="ok")


if __name__ == "__main__":
    with TestClient(app) as client:
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        assert client.get("/openapi.json").json()["paths"]["/healthz"]
    print("PASS FastAPI health response and OpenAPI")
