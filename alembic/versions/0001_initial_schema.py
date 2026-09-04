"""schema inicial: users, instructors, categories, gym_schedules, gym_classes, bookings

Revision ID: 0001
Revises:
Create Date: 2026-01-01 00:00:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    user_role = sa.Enum("student", "admin", name="userrole")
    booking_status = sa.Enum("confirmed", "cancelled", name="bookingstatus")

    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", user_role, nullable=False, server_default="student"),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "instructors",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("specialty", sa.String(120), nullable=True),
        sa.Column("bio", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_instructors_email", "instructors", ["email"])

    op.create_table(
        "categories",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(80), nullable=False, unique=True),
        sa.Column("description", sa.Text, nullable=True),
    )

    op.create_table(
        "gym_schedules",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("category_id", sa.Integer, sa.ForeignKey("categories.id"), nullable=False),
        sa.Column("instructor_id", sa.Integer, sa.ForeignKey("instructors.id"), nullable=False),
        sa.Column("day_of_week", sa.Integer, nullable=False),
        sa.Column("start_time", sa.Time, nullable=False),
        sa.Column("end_time", sa.Time, nullable=False),
        sa.Column("capacity", sa.Integer, nullable=False, server_default="20"),
    )

    op.create_table(
        "gym_classes",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("category_id", sa.Integer, sa.ForeignKey("categories.id"), nullable=False),
        sa.Column("instructor_id", sa.Integer, sa.ForeignKey("instructors.id"), nullable=False),
        sa.Column("schedule_id", sa.Integer, sa.ForeignKey("gym_schedules.id"), nullable=True),
        sa.Column("start_time", sa.DateTime, nullable=False),
        sa.Column("end_time", sa.DateTime, nullable=False),
        sa.Column("capacity", sa.Integer, nullable=False, server_default="20"),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("class_id", sa.Integer, sa.ForeignKey("gym_classes.id"), nullable=False),
        sa.Column("status", booking_status, nullable=False, server_default="confirmed"),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("cancelled_at", sa.DateTime, nullable=True),
        sa.UniqueConstraint("user_id", "class_id", name="uq_user_class_booking"),
    )


def downgrade() -> None:
    op.drop_table("bookings")
    op.drop_table("gym_classes")
    op.drop_table("gym_schedules")
    op.drop_table("categories")
    op.drop_index("ix_instructors_email", table_name="instructors")
    op.drop_table("instructors")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    sa.Enum(name="userrole").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="bookingstatus").drop(op.get_bind(), checkfirst=True)
