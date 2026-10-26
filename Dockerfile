FROM node:24-alpine AS frontend-build
WORKDIR /build/frontend
COPY server/frontend/package.json server/frontend/package-lock.json ./
RUN npm ci
COPY server/frontend/ ./
RUN npm run build

FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_DEBUG=0 \
    DB_PATH=/data/db.sqlite3
WORKDIR /app
COPY server/requirements.txt ./requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY server/ ./
COPY --from=frontend-build /build/frontend/dist ./frontend/dist
RUN DJANGO_SECRET_KEY=build-only-not-a-runtime-secret python manage.py collectstatic --noinput \
    && useradd --create-home --shell /usr/sbin/nologin app \
    && mkdir -p /data \
    && chown app:app /data
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8000/djangoapp/health', headers={'X-Forwarded-Proto':'https'}), timeout=3)"
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py seed_course_data && gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --access-logfile - --error-logfile -"]
