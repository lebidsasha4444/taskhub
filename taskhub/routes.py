from flask import Blueprint, render_template, request
from sqlalchemy.exc import IntegrityError

from .extensions import db
from .models import Task, User

main = Blueprint("main", __name__)


@main.get("/health")
def health() -> str:
    return render_template("health.html")


@main.get("/users")
def list_users() -> str:
    users = db.session.scalars(db.select(User).order_by(User.id)).all()
    return render_template("users.html", users=users)


@main.post("/users")
def create_user() -> str | tuple[str, int]:
    username = request.form.get("username", "")
    if not username.strip():
        return _error_response("username is required", 400)

    user = User(username=username.strip())
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error_response("username already exists", 409)

    users = db.session.scalars(db.select(User).order_by(User.id)).all()
    return render_template("users.html", users=users)


@main.post("/users/<int:user_id>/tasks")
def create_task(user_id: int) -> str | tuple[str, int]:
    title = request.form.get("title", "")
    content = request.form.get("content", "")
    if not title.strip():
        return _error_response("title is required", 400)
    if not content.strip():
        return _error_response("content is required", 400)

    user = db.session.get(User, user_id)
    if user is None:
        return _error_response("user not found", 404)

    task = Task(title=title.strip(), content=content.strip(), user=user)
    db.session.add(task)
    db.session.commit()

    tasks = db.session.scalars(
        db.select(Task).where(Task.user_id == user_id).order_by(Task.id)
    ).all()
    return render_template("tasks.html", user=user, tasks=tasks)


@main.get("/users/<int:user_id>/tasks")
def list_tasks(user_id: int) -> str | tuple[str, int]:
    user = db.session.get(User, user_id)
    if user is None:
        return _error_response("user not found", 404)

    tasks = db.session.scalars(
        db.select(Task).where(Task.user_id == user_id).order_by(Task.id)
    ).all()
    return render_template("tasks.html", user=user, tasks=tasks)


@main.get("/tasks/<int:task_id>")
def get_task(task_id: int) -> str | tuple[str, int]:
    task = db.session.get(Task, task_id)
    if task is None:
        return _error_response("task not found", 404)
    return render_template("task_detail.html", task=task)


def _error_response(message: str, status: int) -> tuple[str, int]:
    return render_template("error.html", message=message), status
