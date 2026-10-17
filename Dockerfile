FROM node:22-bookworm-slim@sha256:c3de60bf2f9dd0ac6370e6117950ff62d6e339527e7472301c9c78a017978392 AS frontend
WORKDIR /build/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.14-slim-bookworm@sha256:48b13b003dda20b16f9442b8475aa05fe21bf6579a8c881db92ffb4d8fd20f83
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY backend/requirements.lock ./requirements.lock
RUN pip install --no-cache-dir -r requirements.lock
COPY backend/ ./backend/
COPY queries/ ./queries/
COPY fixtures/ ./fixtures/
COPY --from=frontend /build/frontend/dist ./frontend/dist
RUN useradd --uid 10001 --create-home mosaic && mkdir /data && chown mosaic:mosaic /data
USER mosaic
EXPOSE 8000
CMD ["uvicorn","backend.app.main:app","--host","0.0.0.0","--port","8000","--no-access-log","--log-level","critical"]
