FROM python:3.13-slim AS build

WORKDIR /app
COPY requirements.txt .
RUN python -m venv /opt/venv \
    && /opt/venv/bin/python -m pip install --no-cache-dir -r requirements.txt

FROM python:3.13-slim AS runtime

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY --from=build /opt/venv /opt/venv
COPY main.py projects.py ./

USER 10001:10001
EXPOSE 8080

CMD ["/opt/venv/bin/python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]