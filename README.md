# ExpenseFlow – Full-Stack Expense Tracker

Flask + SQLAlchemy + SQLite + Bootstrap + Chart.js.

## Run locally
```bash
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python seed.py        # optional demo data (demo@expenseflow.com / demo123)
python app.py         # http://127.0.0.1:5000
```

## Features
Auth (hashed passwords) · expense CRUD · search & filters · monthly budget with warnings ·
Doughnut / Bar / Line charts · spending insights · REST API.

## REST API (login session required)
| Method | Endpoint | Purpose |
|---|---|---|
| GET | /api/expenses | List (supports ?category=&from=&to=&min=&max=&q=) |
| POST | /api/expenses | Create (JSON) |
| PUT | /api/expenses/<id> | Update |
| DELETE | /api/expenses/<id> | Delete |
| GET | /api/expenses/summary | Dashboard totals, charts data, insights |

## Deploy (Render / PythonAnywhere)
Set `SECRET_KEY` env var. For Render add `gunicorn` to requirements and use start command `gunicorn app:app`.

## Production checklist
- Set `APP_ENV=production` and a long random `SECRET_KEY` (see `.env.example`); the app refuses to start without it.
- Use PostgreSQL via `DATABASE_URL` (Render/Railway/Heroku `postgres://` URLs are handled).
- Start with `gunicorn app:app` (see `Procfile`). Serve over HTTPS: secure cookies and HSTS are enabled automatically.
- Built in: CSRF protection, security headers, hashed passwords, per-user data isolation, error pages.
