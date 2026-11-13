from fastapi import FastAPI

app = FastAPI(title="Acadence Notification Service")


@app.get("/healthz")
def health() -> dict[str, str]:
    return {"status": "ok"}

@app.get("/readyz")
def readiness() -> dict[str, str]:
    return {"status": "ready"}
