# fullstack_developer_capstone

- **Repository name:** `xrwvm-fullstack_developer_capstone`
- **Project name:** `fullstack_developer_capstone`

A Django and React dealership directory for browsing dealership records, vehicle make/model pairs, and customer reviews.

## Features

- Django REST API and React user interface
- Dealer details, state filtering, and course review records
- Session registration, login, logout, and authenticated review posting
- VADER sentiment analysis
- Course car make/model catalog
- Django admin and CI lint workflow
- Docker and Render Blueprint deployment configuration

## Run locally

Requirements: Python 3.13+, Node.js 22+, npm.

```powershell
cd server
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_course_data
python3 manage.py runserver
```

In a second terminal, build or run the React application:

```powershell
cd server/frontend
npm ci
npm run build
```

The Django server serves the built React pages at `http://127.0.0.1:8000`. For Vite development, run `npm run dev` and open `http://127.0.0.1:5173`.

Create an admin account locally with `python manage.py createsuperuser`. Do not commit credentials.

## Course endpoints

- `GET /fetchDealers`
- `GET /fetchDealers/Kansas`
- `GET /fetchDealer/1`
- `GET /fetchReviews/dealer/1`
- `GET /analyze/Fantastic%20services`
- `POST /djangoapp/login` with JSON `userName` and `password`
- `GET /djangoapp/logout`
- `GET /djangoapp/get_cars`

The official course dealer, review, and car records are under `server/database/data`. Load them with `python manage.py seed_course_data`.

## Docker

Copy `server/.env.example` to `server/.env`, set a private production secret and host/origin values, then run `docker compose up --build`. The image builds the frontend, applies migrations, loads the course records, and serves Django through Gunicorn.

## Deployment

`render.yaml` defines a Docker web service with a generated Django secret and health check. Create a Render Blueprint from this repository to obtain its real public HTTPS URL. Free Render services use ephemeral storage, so locally saved SQLite changes can disappear after a restart; the published course records are reloaded at startup.

## Attribution

The dealership, review, and car catalog fixtures are from the IBM Full Stack Developer Capstone starter data. Sentiment analysis uses VADER.
