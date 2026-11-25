from datetime import UTC, date, datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship

from .extensions import db


class User(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(db.String(80), unique=True, nullable=False)
    email: Mapped[str | None] = mapped_column(db.String(254), unique=True)
    password_hash: Mapped[str | None] = mapped_column(db.String(256))
    tasks: Mapped[list["Task"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Task(db.Model):
    __table_args__ = (
        db.CheckConstraint(
            "priority IN ('low', 'middle', 'high')",
            name="ck_task_priority",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(db.String(200), nullable=False)
    content: Mapped[str] = mapped_column(db.Text, nullable=False)
    priority: Mapped[str] = mapped_column(
        db.String(10),
        default="middle",
        nullable=False,
    )
    due_date: Mapped[date | None] = mapped_column(db.Date)
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        db.ForeignKey("user.id"),
        nullable=False,
        index=True,
    )
    user: Mapped[User] = relationship(back_populates="tasks")
