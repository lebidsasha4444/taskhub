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
flask --app taskhub run
python main.py
```

The health check is available at `GET /health`.

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

Initialize the migration repository once, then create and apply migrations as
models are added:

```powershell
flask --app taskhub db init
flask --app taskhub db migrate -m "Describe schema change"
flask --app taskhub db upgrade
```

Import model modules from `taskhub/models.py` so Flask-Migrate can find their
metadata. Do not use `db.create_all()` as a replacement for migrations.

## Tests

```powershell
python -m unittest discover -s tests -v
```