"""Add authentication schema."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002_authentication"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=512), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False, server_default="user"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    with op.batch_alter_table("documents") as batch_op:
        batch_op.add_column(sa.Column("created_by_user_id", sa.String(length=36), nullable=True))
        batch_op.create_foreign_key(
            "fk_documents_created_by_user_id",
            "users",
            ["created_by_user_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index("ix_documents_created_by_user_id", ["created_by_user_id"])

    with op.batch_alter_table("index_jobs") as batch_op:
        batch_op.add_column(sa.Column("created_by_user_id", sa.String(length=36), nullable=True))
        batch_op.create_foreign_key(
            "fk_index_jobs_created_by_user_id",
            "users",
            ["created_by_user_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index("ix_index_jobs_created_by_user_id", ["created_by_user_id"])

    with op.batch_alter_table("query_logs") as batch_op:
        batch_op.add_column(sa.Column("created_by_user_id", sa.String(length=36), nullable=True))
        batch_op.create_foreign_key(
            "fk_query_logs_created_by_user_id",
            "users",
            ["created_by_user_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index("ix_query_logs_created_by_user_id", ["created_by_user_id"])


def downgrade() -> None:
    with op.batch_alter_table("query_logs") as batch_op:
        batch_op.drop_index("ix_query_logs_created_by_user_id")
        batch_op.drop_constraint("fk_query_logs_created_by_user_id", type_="foreignkey")
        batch_op.drop_column("created_by_user_id")

    with op.batch_alter_table("index_jobs") as batch_op:
        batch_op.drop_index("ix_index_jobs_created_by_user_id")
        batch_op.drop_constraint("fk_index_jobs_created_by_user_id", type_="foreignkey")
        batch_op.drop_column("created_by_user_id")

    with op.batch_alter_table("documents") as batch_op:
        batch_op.drop_index("ix_documents_created_by_user_id")
        batch_op.drop_constraint("fk_documents_created_by_user_id", type_="foreignkey")
        batch_op.drop_column("created_by_user_id")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
