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

## Users and notes

Open `/users` to create users and browse their notes (stored as `Task` records).
Use the forms on each page to create a user or add a note. Select a user to view
their notes, or select a note to view its content. Routes render HTML templates;
they do not provide JSON API responses.

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
