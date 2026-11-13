FROM python:3.13-slim AS build

WORKDIR /app
COPY main.py .

FROM python:3.13-slim AS runtime

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY --from=build /app/main.py .

USER 10001:10001

ENTRYPOINT ["python", "main.py"]
