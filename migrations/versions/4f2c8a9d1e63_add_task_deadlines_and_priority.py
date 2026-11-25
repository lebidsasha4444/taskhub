"""Add task deadlines and priority

Revision ID: 4f2c8a9d1e63
Revises: a976df7d7302
Create Date: 2026-11-18 12:45:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "4f2c8a9d1e63"
down_revision = "a976df7d7302"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("task", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "priority",
                sa.String(length=10),
                server_default="middle",
                nullable=False,
            )
        )
        batch_op.add_column(sa.Column("due_date", sa.Date(), nullable=True))
        batch_op.create_check_constraint(
            "ck_task_priority",
            "priority IN ('low', 'middle', 'high')",
        )
        batch_op.alter_column("priority", server_default=None)


def downgrade():
    with op.batch_alter_table("task", schema=None) as batch_op:
        batch_op.drop_constraint("ck_task_priority", type_="check")
        batch_op.drop_column("due_date")
        batch_op.drop_column("priority")
