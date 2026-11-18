# Taskhub

## Setup

Create and activate a virtual environment, then install dependencies:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Run the app with Flask's CLI (which loads `.env`) or directly:

```powershell
flask --app taskhub db upgrade
flask --app taskhub run
python main.py
```

The status page is available at `GET /health`.

## Accounts and notes

Open `/register` to create an account with a username, email address, and
password, or sign in at `/login`. Passwords are stored as hashes. Successful
registration and sign-in open the overview dashboard. Use the left navigation
to view the dashboard or your tasks, create tasks with a deadline and low,
middle, or high priority, and sign out. Selecting a task opens its full details.
Routes render HTML templates; they do not provide JSON API responses. Set
`SECRET_KEY` to a stable, private value in `.env` for sessions to remain valid
across application restarts.

## Architecture

- `taskhub/__init__.py` creates the Flask app and connects extensions.
- `taskhub/config.py` reads runtime settings from environment variables.
- `taskhub/extensions.py` owns shared SQLAlchemy and migration extensions.
- `taskhub/models.py` is the model registration point for migrations.
- `taskhub/routes.py` contains the main blueprint and HTTP routes.
- `main.py` exposes the app factory result for local execution and WSGI servers.

SQLite is the default database (`instance/taskhub.db`). Set `DATABASE_URL` to
use another SQLAlchemy-supported database URI. `DEBUG` is parsed as a boolean.

## Database migrations

The initial schema migration is included. Apply it before the first run with
`flask --app taskhub db upgrade`. When models change, generate and apply a
migration:

```powershell
flask --app taskhub db migrate -m "Describe schema change"
flask --app taskhub db upgrade
```

Run `flask --app taskhub db init` only when creating a new migration repository.
Import model modules from `taskhub/models.py` so Flask-Migrate can find their
metadata. Do not use `db.create_all()` as a replacement for migrations.

## Tests

```powershell
python -m unittest discover -s tests -v
```
