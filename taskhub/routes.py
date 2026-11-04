from sqlalchemy.exc import IntegrityError
from flask import Blueprint, request

from .extensions import db
from .models import Task, User

main = Blueprint("main", __name__)


@main.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@main.post("/users")
def create_user() -> tuple[dict[str, object], int]:
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return {"error": "Request body must be a JSON object"}, 400

    username = payload.get("username")
    if not isinstance(username, str) or not username.strip():
        return {"error": "username is required"}, 400

    user = User(username=username.strip())
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"error": "username already exists"}, 409

    return {"id": user.id, "username": user.username}, 201


@main.post("/users/<int:user_id>/tasks")
def create_task(user_id: int) -> tuple[dict[str, object], int]:
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return {"error": "Request body must be a JSON object"}, 400

    title = payload.get("title")
    content = payload.get("content")
    if not isinstance(title, str) or not title.strip():
        return {"error": "title is required"}, 400
    if not isinstance(content, str) or not content.strip():
        return {"error": "content is required"}, 400

    user = db.session.get(User, user_id)
    if user is None:
        return {"error": "user not found"}, 404

    task = Task(title=title.strip(), content=content.strip(), user=user)
    db.session.add(task)
    db.session.commit()
    return _task_data(task), 201


@main.get("/users/<int:user_id>/tasks")
def list_tasks(user_id: int) -> tuple[list[dict[str, object]] | dict[str, str], int]:
    if db.session.get(User, user_id) is None:
        return {"error": "user not found"}, 404

    tasks = db.session.scalars(
        db.select(Task).where(Task.user_id == user_id).order_by(Task.id)
    ).all()
    return [_task_data(task) for task in tasks], 200


@main.get("/tasks/<int:task_id>")
def get_task(task_id: int) -> tuple[dict[str, object], int] | tuple[dict[str, str], int]:
    task = db.session.get(Task, task_id)
    if task is None:
        return {"error": "task not found"}, 404
    return _task_data(task), 200


def _task_data(task: Task) -> dict[str, object]:
    return {
        "id": task.id,
        "title": task.title,
        "content": task.content,
        "created_at": task.created_at.isoformat(),
        "user_id": task.user_id,
    }
