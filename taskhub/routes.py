import re
from datetime import date, timedelta

from flask import Blueprint, redirect, render_template, request, session, url_for
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db
from .models import Task, User

main = Blueprint("main", __name__)


@main.app_context_processor
def inject_current_user() -> dict[str, User | None]:
    return {"current_user": _current_user()}


@main.get("/")
@main.get("/login")
def login() -> str:
    if _current_user() is not None:
        return redirect(url_for("main.overview", user_id=session["user_id"]))
    return render_template(
        "auth.html",
        mode="login",
        registered=request.args.get("registered") == "1",
    )


@main.post("/login")
def authenticate() -> str | tuple[str, int]:
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    user = db.session.scalar(db.select(User).where(db.func.lower(User.email) == email))
    if (
        user is None
        or user.password_hash is None
        or not check_password_hash(user.password_hash, password)
    ):
        return render_template(
            "auth.html",
            mode="login",
            error="The email or password is incorrect.",
        ), 401

    session.clear()
    session["user_id"] = user.id
    return redirect(url_for("main.overview", user_id=user.id))


@main.get("/register")
def register() -> str:
    if _current_user() is not None:
        return redirect(url_for("main.overview", user_id=session["user_id"]))
    return render_template("auth.html", mode="register")


@main.post("/register")
def create_account() -> str | tuple[str, int]:
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    password_confirmation = request.form.get("confirm_password", "")

    if not username or len(username) > 80:
        return _auth_error("Enter a username with at most 80 characters.")
    if len(email) > 254 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        return _auth_error("Enter a valid email address.")
    if len(password) < 8 or len(password) > 128:
        return _auth_error("Password must be between 8 and 128 characters.")
    if password != password_confirmation:
        return _auth_error("Passwords do not match.")

    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
    )
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _auth_error("That username or email is already registered.", 409)

    session.clear()
    session["user_id"] = user.id
    return redirect(url_for("main.overview", user_id=user.id))


@main.post("/logout")
def logout() -> str:
    session.clear()
    return redirect(url_for("main.login"))


@main.get("/health")
def health() -> str:
    return render_template("health.html")


@main.get("/users")
def list_users() -> str:
    user = _current_user()
    if user is None:
        return redirect(url_for("main.login"))
    return redirect(url_for("main.overview", user_id=user.id))


@main.get("/users/<int:user_id>/overview")
def overview(user_id: int) -> str | tuple[str, int]:
    user = _current_user()
    if user is None:
        return redirect(url_for("main.login"))
    if user.id != user_id:
        return _error_response("user not found", 404)

    task_count = db.session.scalar(
        db.select(db.func.count(Task.id)).where(Task.user_id == user_id)
    )
    high_priority_count = db.session.scalar(
        db.select(db.func.count(Task.id)).where(
            Task.user_id == user_id,
            Task.priority == "high",
        )
    )
    today = date.today()
    upcoming_count = db.session.scalar(
        db.select(db.func.count(Task.id)).where(
            Task.user_id == user_id,
            Task.due_date >= today,
            Task.due_date <= today + timedelta(days=7),
        )
    )
    recent_tasks = db.session.scalars(
        db.select(Task)
        .where(Task.user_id == user_id)
        .order_by(Task.created_at.desc(), Task.id.desc())
        .limit(3)
    ).all()
    return render_template(
        "overview.html",
        user=user,
        task_count=task_count or 0,
        high_priority_count=high_priority_count or 0,
        upcoming_count=upcoming_count or 0,
        recent_tasks=recent_tasks,
    )


@main.post("/users/<int:user_id>/tasks")
def create_task(user_id: int) -> str | tuple[str, int]:
    user = _current_user()
    if user is None:
        return redirect(url_for("main.login"))
    if user.id != user_id:
        return _error_response("user not found", 404)

    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    raw_due_date = request.form.get("due_date", "")
    priority = request.form.get("priority", "")
    if not title.strip():
        return _task_form_error(user, "A title is required.")
    if len(title) > 200:
        return _task_form_error(user, "The title must be 200 characters or fewer.")
    if not content:
        return _task_form_error(user, "Task details are required.")
    if not raw_due_date:
        return _task_form_error(user, "Choose a deadline for this task.")
    try:
        due_date = date.fromisoformat(raw_due_date)
    except ValueError:
        return _task_form_error(user, "Enter a valid deadline.")
    if priority not in {"low", "middle", "high"}:
        return _task_form_error(user, "Choose a valid priority.")

    task = Task(
        title=title,
        content=content,
        due_date=due_date,
        priority=priority,
        user=user,
    )
    db.session.add(task)
    db.session.commit()

    tasks = db.session.scalars(
        db.select(Task)
        .where(Task.user_id == user_id)
        .order_by(Task.created_at.desc(), Task.id.desc())
    ).all()
    return render_template("tasks.html", user=user, tasks=tasks)


@main.get("/users/<int:user_id>/tasks")
def list_tasks(user_id: int) -> str | tuple[str, int]:
    user = _current_user()
    if user is None:
        return redirect(url_for("main.login"))
    if user.id != user_id:
        return _error_response("user not found", 404)

    tasks = db.session.scalars(
        db.select(Task)
        .where(Task.user_id == user_id)
        .order_by(Task.created_at.desc(), Task.id.desc())
    ).all()
    return render_template("tasks.html", user=user, tasks=tasks)


@main.get("/tasks/<int:task_id>")
def get_task(task_id: int) -> str | tuple[str, int]:
    user = _current_user()
    if user is None:
        return redirect(url_for("main.login"))
    task = db.session.get(Task, task_id)
    if task is None:
        return _error_response("task not found", 404)
    if task.user_id != user.id:
        return _error_response("task not found", 404)
    return render_template("task_detail.html", task=task, user=user)


def _current_user() -> User | None:
    user_id = session.get("user_id")
    if not isinstance(user_id, int):
        return None
    return db.session.get(User, user_id)


def _auth_error(message: str, status: int = 400) -> tuple[str, int]:
    return render_template("auth.html", mode="register", error=message), status


def _task_form_error(user: User, message: str) -> tuple[str, int]:
    tasks = db.session.scalars(
        db.select(Task)
        .where(Task.user_id == user.id)
        .order_by(Task.created_at.desc(), Task.id.desc())
    ).all()
    return (
        render_template(
            "tasks.html",
            user=user,
            tasks=tasks,
            error=message,
            show_create_modal=True,
        ),
        400,
    )


def _error_response(message: str, status: int) -> tuple[str, int]:
    return render_template("error.html", message=message), status
