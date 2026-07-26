"""Convert all varchar UUID columns to native PostgreSQL uuid type.

All DeviceLab-specific tables had their UUID columns created as
character varying instead of native uuid because of a migration
scaffolding fix. This causes SQLAlchemy to fail at runtime because
the models declare these fields as uuid.UUID, which makes SQLAlchemy
generate `= $1::UUID` casts that PostgreSQL rejects against varchar columns.

This migration:
  1. Drops all FK constraints that touch UUID columns
  2. Converts each varchar UUID column to native uuid with USING col::uuid
  3. Re-adds the FK constraints

Non-UUID varchar columns (account_id, target_id, session_id, client_id,
scope_id, provider_snapshot_id) are deliberately NOT converted.

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2026-06-06
"""

from alembic import op

revision = "c4d5e6f7a8b9"
down_revision = "b3c4d5e6f7a8"
branch_labels = None
depends_on = None


# ---------------------------------------------------------------------------
# FK constraints that must be dropped before altering column types and
# re-created afterward.  Order: child table first on drop, any order on create.
# ---------------------------------------------------------------------------
FK_CONSTRAINTS = [
    # (child_table, constraint_name, child_cols, parent_table, parent_cols)
    ("cloudaccount",  "cloudaccount_workspace_id_fkey",  ["workspace_id"], "workspace",      ["id"]),
    ("device",        "device_template_id_fkey",         ["template_id"],  "devicetemplate", ["id"]),
    ("device",        "device_workspace_id_fkey",        ["workspace_id"], "workspace",      ["id"]),
    ("auditevent",    "auditevent_workspace_id_fkey",     ["workspace_id"], "workspace",      ["id"]),
    ("secretref",     "secretref_workspace_id_fkey",     ["workspace_id"], "workspace",      ["id"]),
    ("recipe",        "recipe_workspace_id_fkey",        ["workspace_id"], "workspace",      ["id"]),
    ("reciperun",     "reciperun_recipe_id_fkey",        ["recipe_id"],    "recipe",         ["id"]),
    ("costpolicy",    "costpolicy_workspace_id_fkey",    ["workspace_id"], "workspace",      ["id"]),
    ("snapshot",      "snapshot_workspace_id_fkey",      ["workspace_id"], "workspace",      ["id"]),
    ("artifact",      "artifact_workspace_id_fkey",      ["workspace_id"], "workspace",      ["id"]),
    ("testrun",       "testrun_workspace_id_fkey",       ["workspace_id"], "workspace",      ["id"]),
    ("devicemanifest","devicemanifest_workspace_id_fkey",["workspace_id"], "workspace",      ["id"]),
    ("appsetting",    "appsetting_workspace_id_fkey",    ["workspace_id"], "workspace",      ["id"]),
]

# ---------------------------------------------------------------------------
# (table, column) pairs to convert varchar → uuid.
# Nullable columns convert fine: NULL::uuid stays NULL.
# ---------------------------------------------------------------------------
UUID_COLUMNS = [
    # Root table — must go first because others FK into it
    ("workspace",      "id"),

    ("cloudaccount",   "id"),
    ("cloudaccount",   "workspace_id"),

    ("devicetemplate", "id"),

    ("device",         "id"),
    ("device",         "template_id"),
    ("device",         "workspace_id"),
    ("device",         "source_manifest_id"),

    ("hostreservation","id"),
    ("hostreservation","device_id"),

    ("devicelogevent", "id"),
    ("devicelogevent", "device_id"),

    ("auditevent",     "id"),
    ("auditevent",     "workspace_id"),
    # NOTE: auditevent.target_id is str — not converted

    ("devicemanifest", "id"),
    ("devicemanifest", "workspace_id"),
    ("devicemanifest", "source_device_id"),

    ("evidence",       "id"),
    ("evidence",       "device_id"),
    ("evidence",       "audit_event_id"),
    # NOTE: evidence.session_id is str — not converted

    ("secretref",      "id"),
    ("secretref",      "workspace_id"),

    ("recipe",         "id"),
    ("recipe",         "workspace_id"),

    ("reciperun",      "id"),
    ("reciperun",      "recipe_id"),
    ("reciperun",      "device_id"),

    ("streamsession",  "id"),
    ("streamsession",  "device_id"),
    # NOTE: streamsession.client_id is str — not converted

    ("costpolicy",     "id"),
    ("costpolicy",     "workspace_id"),
    # NOTE: costpolicy.scope_id is str — not converted

    ("snapshot",       "id"),
    ("snapshot",       "workspace_id"),
    ("snapshot",       "source_device_id"),
    # NOTE: snapshot.provider_snapshot_id is str — not converted

    ("artifact",       "id"),
    ("artifact",       "workspace_id"),
    ("artifact",       "run_id"),
    ("artifact",       "evidence_id"),
    # NOTE: artifact.session_id is str — not converted

    ("testrun",        "id"),
    ("testrun",        "workspace_id"),
    ("testrun",        "device_id"),
    ("testrun",        "recipe_id"),
    ("testrun",        "recipe_run_id"),

    ("appsetting",     "id"),
    ("appsetting",     "workspace_id"),
]


def upgrade() -> None:
    # 1. Drop FK constraints
    for child_table, constraint_name, _, _, _ in FK_CONSTRAINTS:
        op.drop_constraint(constraint_name, child_table, type_="foreignkey")

    # 2. Convert columns — USING col::uuid handles empty tables and NULLs
    for table, column in UUID_COLUMNS:
        op.execute(
            f'ALTER TABLE "{table}" '
            f'ALTER COLUMN "{column}" TYPE uuid '
            f'USING "{column}"::uuid'
        )

    # 3. Re-add FK constraints (types now match on both sides)
    for child_table, constraint_name, child_cols, parent_table, parent_cols in FK_CONSTRAINTS:
        op.create_foreign_key(
            constraint_name,
            child_table,
            parent_table,
            child_cols,
            parent_cols,
        )


def downgrade() -> None:
    # 1. Drop FK constraints
    for child_table, constraint_name, _, _, _ in FK_CONSTRAINTS:
        op.drop_constraint(constraint_name, child_table, type_="foreignkey")

    # 2. Convert back to varchar (lossy only if data existed — dev env is fine)
    for table, column in UUID_COLUMNS:
        op.execute(
            f'ALTER TABLE "{table}" '
            f'ALTER COLUMN "{column}" TYPE character varying '
            f'USING "{column}"::character varying'
        )

    # 3. Re-add FK constraints
    for child_table, constraint_name, child_cols, parent_table, parent_cols in FK_CONSTRAINTS:
        op.create_foreign_key(
            constraint_name,
            child_table,
            parent_table,
            child_cols,
            parent_cols,
        )
