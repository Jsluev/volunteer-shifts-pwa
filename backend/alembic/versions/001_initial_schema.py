"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-07-24
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, ARRAY

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("slug", sa.Text, unique=True, nullable=False),
        sa.Column("timezone", sa.Text, server_default="Europe/Moscow"),
        sa.Column("settings", JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now()),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.Integer, sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.Text, nullable=False),
        sa.Column("phone", sa.Text),
        sa.Column("role", sa.Text, nullable=False),
        sa.Column("full_name", sa.Text),
        sa.Column("password_hash", sa.Text, nullable=False),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now()),
    )
    op.create_index("idx_users_tenant_role", "users", ["tenant_id", "role"])

    op.create_table(
        "departments",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.Integer, sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "name", name="uq_departments_tenant_name"),
    )

    op.create_table(
        "shifts",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.Integer, sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("department_id", sa.Integer, sa.ForeignKey("departments.id"), nullable=False),
        sa.Column("start_time", sa.TIMESTAMP, nullable=False),
        sa.Column("end_time", sa.TIMESTAMP, nullable=False),
        sa.Column("total_slots", sa.Integer, nullable=False),
        sa.Column("status", sa.Text, nullable=False, server_default="draft"),
        sa.Column("created_by", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now()),
        sa.CheckConstraint("total_slots > 0", name="ck_shifts_total_slots_positive"),
    )
    op.create_index("idx_shifts_tenant_date", "shifts", ["tenant_id", "start_time"], postgresql_where="status = 'published'")

    op.create_table(
        "shift_registrations",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("shift_id", sa.Integer, sa.ForeignKey("shifts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.Text, nullable=False, server_default="pending"),
        sa.Column("moderator_comment", sa.Text),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP, server_default=sa.func.now()),
        sa.UniqueConstraint("shift_id", "user_id", name="uq_shift_registrations_shift_user"),
    )
    op.create_index("idx_reg_shift_status", "shift_registrations", ["shift_id", "status"], postgresql_where="status IN ('approved', 'attendance_confirmed')")
    op.create_index("idx_reg_user_active", "shift_registrations", ["user_id", "status"], postgresql_where="status IN ('approved', 'attendance_confirmed', 'pending')")

    op.create_table(
        "dialogs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.Integer, sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.Text, nullable=False),
        sa.Column("participant_ids", ARRAY(sa.Integer)),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now()),
    )

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("dialog_id", sa.Integer, sa.ForeignKey("dialogs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sender_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now()),
    )
    op.create_index("idx_chat_messages_dialog_created", "chat_messages", ["dialog_id", "created_at"])

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("type", sa.Text, nullable=False),
        sa.Column("channel", sa.Text, nullable=False),
        sa.Column("subject", sa.Text),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("scheduled_at", sa.TIMESTAMP, nullable=False),
        sa.Column("sent_at", sa.TIMESTAMP),
        sa.Column("status", sa.Text, nullable=False, server_default="pending"),
        sa.Column("retry_count", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now()),
    )
    op.create_index("idx_notif_scheduled", "notifications", ["scheduled_at"], postgresql_where="status = 'pending'")

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.Integer, sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("action_type", sa.Text, nullable=False),
        sa.Column("meta", JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now()),
    )
    op.create_index("idx_audit_coord_created", "audit_logs", ["tenant_id", "user_id", "created_at"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("notifications")
    op.drop_table("chat_messages")
    op.drop_table("dialogs")
    op.drop_table("shift_registrations")
    op.drop_table("shifts")
    op.drop_table("departments")
    op.drop_table("users")
    op.drop_table("tenants")
