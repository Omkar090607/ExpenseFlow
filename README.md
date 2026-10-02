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

## Deploy to Vercel (free tier)

1. Push this project to a GitHub repository and import it in Vercel.
2. Create a free PostgreSQL database with a provider such as Neon. Copy its connection URL; use the pooled URL if the provider offers one, and ensure it includes `sslmode=require`.
3. In Vercel, open **Project Settings → Environment Variables** and add:
	- `APP_ENV` = `production`
	- `SECRET_KEY` = a long, random secret
	- `DATABASE_URL` = the PostgreSQL connection URL
4. Deploy (or redeploy after setting the variables). Vercel will install `requirements.txt`; the app creates its tables on startup.

Do not use the default SQLite database for a Vercel deployment: serverless files are temporary, so SQLite data would not persist between invocations. PostgreSQL is required for saved accounts, expenses, and budgets.

## Deploy (Render / PythonAnywhere)
Set `SECRET_KEY` env var. For Render add `gunicorn` to requirements and use start command `gunicorn app:app`.

## Production checklist
- Set `APP_ENV=production` and a long random `SECRET_KEY` (see `.env.example`); the app refuses to start without it.
- Use PostgreSQL via `DATABASE_URL` (Render/Railway/Heroku `postgres://` URLs are handled).
- Start with `gunicorn app:app` (see `Procfile`). Serve over HTTPS: secure cookies and HSTS are enabled automatically.
- Built in: CSRF protection, security headers, hashed passwords, per-user data isolation, error pages.
