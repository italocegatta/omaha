"""Add profile-scoped MyProfit synchronization lifecycle rows."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0020_myprofit_sync_jobs"
down_revision = "0019_asset_target_pct_precision"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "myprofit_sync_jobs",
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("preview_id", sa.Integer(), nullable=True),
        sa.Column("filename", sa.String(length=128), nullable=True),
        sa.Column("error_stage", sa.String(length=32), nullable=True),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("work_dir", sa.String(length=1024), nullable=True),
        sa.Column("work_file", sa.String(length=1024), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("retention_until", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'failed', 'expired')",
            name="ck_myprofit_sync_job_status",
        ),
        sa.ForeignKeyConstraint(
            ["profile_id"], ["profiles.id"], ondelete="CASCADE", name="fk_myprofit_sync_job_profile"
        ),
        sa.ForeignKeyConstraint(
            ["preview_id"],
            ["import_previews.id"],
            ondelete="SET NULL",
            name="fk_myprofit_sync_job_preview",
        ),
        sa.PrimaryKeyConstraint("job_id"),
    )
    op.create_index(
        "ix_myprofit_sync_jobs_profile_created", "myprofit_sync_jobs", ["profile_id", "created_at"]
    )
    op.create_index(
        "ix_myprofit_sync_jobs_profile_status",
        "myprofit_sync_jobs",
        ["profile_id", "status", "created_at"],
    )
    op.create_index("ix_myprofit_sync_jobs_preview_id", "myprofit_sync_jobs", ["preview_id"])
    op.create_index("ix_myprofit_sync_jobs_expires_at", "myprofit_sync_jobs", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_myprofit_sync_jobs_expires_at", table_name="myprofit_sync_jobs")
    op.drop_index("ix_myprofit_sync_jobs_preview_id", table_name="myprofit_sync_jobs")
    op.drop_index("ix_myprofit_sync_jobs_profile_status", table_name="myprofit_sync_jobs")
    op.drop_index("ix_myprofit_sync_jobs_profile_created", table_name="myprofit_sync_jobs")
    op.drop_table("myprofit_sync_jobs")
