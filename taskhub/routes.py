from flask import Blueprint

main = Blueprint("main", __name__)


@main.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
