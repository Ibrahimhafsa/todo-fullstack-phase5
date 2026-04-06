"""Extend Task model with Phase 5 advanced features (Spec-006).

Revision ID: 001_extend_task_model
Revises:
Create Date: 2026-03-15 00:00:00.000000

This migration adds 6 new optional fields to the Task table for Spec-006
(Advanced Todo Features):
- priority (Low/Medium/High, default: Medium)
- tags (JSON array of strings)
- due_date (optional deadline)
- reminder_time (optional reminder time)
- is_recurring (whether task repeats)
- recurring_pattern (Daily/Weekly/Monthly)

All fields are nullable with sensible defaults for zero-downtime migration.
Existing data continues to work unchanged.

Constitution Principles:
- Phase 2 Lockdown (XVI): No existing fields modified or removed
- Task Ownership (VII): No ownership logic changes needed
- Event-Driven (XXVI): Events will be published by Phase 2.2

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "001_extend_task_model"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add 6 new optional fields to tasks table."""
    # priority: enum(Low/Medium/High) with default 'Medium'
    op.add_column(
        "tasks",
        sa.Column(
            "priority",
            sa.String(length=20),
            server_default="Medium",
            nullable=False,
        ),
    )

    # tags: JSON array stored as string, default empty array
    op.add_column(
        "tasks",
        sa.Column(
            "tags",
            sa.String(),
            server_default="[]",
            nullable=False,
        ),
    )

    # due_date: optional deadline
    op.add_column(
        "tasks",
        sa.Column(
            "due_date",
            sa.DateTime(),
            nullable=True,
        ),
    )

    # reminder_time: optional reminder scheduling
    op.add_column(
        "tasks",
        sa.Column(
            "reminder_time",
            sa.DateTime(),
            nullable=True,
        ),
    )

    # is_recurring: whether task repeats automatically
    op.add_column(
        "tasks",
        sa.Column(
            "is_recurring",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )

    # recurring_pattern: Daily/Weekly/Monthly recurrence
    op.add_column(
        "tasks",
        sa.Column(
            "recurring_pattern",
            sa.String(length=20),
            nullable=True,
        ),
    )

    # Create indexes for common queries (Phase 2.3 and 2.4)
    # Priority filter: (user_id, priority)
    op.create_index(
        "idx_tasks_user_priority",
        "tasks",
        ["user_id", "priority"],
    )

    # Due date sorting: (user_id, due_date)
    op.create_index(
        "idx_tasks_user_due_date",
        "tasks",
        ["user_id", "due_date"],
    )

    # Recurring task lookups: (user_id, is_recurring)
    op.create_index(
        "idx_tasks_user_recurring",
        "tasks",
        ["user_id", "is_recurring"],
    )

    print("\n✓ Migration: Extended Task model with Phase 5 fields")
    print("  - priority (Low/Medium/High)")
    print("  - tags (JSON array)")
    print("  - due_date (optional deadline)")
    print("  - reminder_time (optional reminder)")
    print("  - is_recurring (boolean)")
    print("  - recurring_pattern (Daily/Weekly/Monthly)")
    print("  - 3 performance indexes created")
    print("  - Backward compatible: all fields have defaults")


def downgrade() -> None:
    """Remove Phase 5 extensions from tasks table."""
    # Drop indexes first
    op.drop_index("idx_tasks_user_recurring", table_name="tasks")
    op.drop_index("idx_tasks_user_due_date", table_name="tasks")
    op.drop_index("idx_tasks_user_priority", table_name="tasks")

    # Remove columns in reverse order
    op.drop_column("tasks", "recurring_pattern")
    op.drop_column("tasks", "is_recurring")
    op.drop_column("tasks", "reminder_time")
    op.drop_column("tasks", "due_date")
    op.drop_column("tasks", "tags")
    op.drop_column("tasks", "priority")

    print("\n✓ Rollback: Removed Phase 5 extensions from Task model")
