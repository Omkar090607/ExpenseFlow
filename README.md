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

## Deploy for free (Render + Neon)

The Flask app runs as a free web service on Render. Use a free PostgreSQL database on Neon for persistent accounts, expenses, and budgets; Render's local filesystem is temporary, so the default SQLite database is not suitable for deployment.

1. Push the project to GitHub.
2. Create a PostgreSQL project on Neon and copy its connection string. Use the pooled connection string if available and ensure it includes `sslmode=require`.
3. In Render, choose **New + → Blueprint**, connect the GitHub repository, and deploy. Render reads `render.yaml` and creates a free web service. When prompted, enter the Neon connection string for `DATABASE_URL`; `APP_ENV` and a generated `SECRET_KEY` are configured by the blueprint.
4. Wait for the deployment to finish, then open the service URL shown in Render.

The free web service may spin down when idle and take a little longer to respond on its first request. Free database plans have provider-specific usage and storage limits; check Neon’s current plan before relying on it for production data.

## Production checklist
- Set `APP_ENV=production` and a long random `SECRET_KEY` (see `.env.example`); the app refuses to start without it.
- Use PostgreSQL via `DATABASE_URL` (`postgres://` URLs are handled).
- Start with `gunicorn app:app` (see `Procfile`). Serve over HTTPS: secure cookies and HSTS are enabled automatically.
- Built in: CSRF protection, security headers, hashed passwords, per-user data isolation, error pages.
