"""fix tenant_id and created_by column types from uuid to bigint

Revision ID: 20260727_0002
Revises: 20260727_0001
Create Date: 2026-07-27
"""

from alembic import op
import sqlalchemy as sa

revision = "20260727_0002"
down_revision = "20260727_0001"
branch_labels = None
depends_on = None

# Every table that has a tenant_id or created_by column currently stored as
# uuid in the database but declared as BigInteger in the ORM models.

_TENANT_ID_TABLES = [
    "t_knowledge_bases",
    "t_documents",
    "t_document_versions",
    "t_document_chunks",
    "t_index_tasks",
    "t_retrieval_logs",
    "t_retrieval_feedback",
]

_CREATED_BY_TABLES = [
    "t_knowledge_bases",
    "t_documents",
    "t_retrieval_feedback",
]


def upgrade() -> None:
    # tenant_id columns: uuid -> bigint
    for table in _TENANT_ID_TABLES:
        op.alter_column(
            table,
            "tenant_id",
            existing_type=sa.dialects.postgresql.UUID(as_uuid=True),
            type_=sa.BigInteger(),
            existing_nullable=False,
            postgresql_using="tenant_id::text::bigint",
        )

    # created_by columns: uuid -> bigint
    for table in _CREATED_BY_TABLES:
        op.alter_column(
            table,
            "created_by",
            existing_type=sa.dialects.postgresql.UUID(as_uuid=True),
            type_=sa.BigInteger(),
            existing_nullable=False,
            postgresql_using="created_by::text::bigint",
        )


def downgrade() -> None:
    for table in _TENANT_ID_TABLES:
        op.alter_column(
            table,
            "tenant_id",
            existing_type=sa.BigInteger(),
            type_=sa.dialects.postgresql.UUID(as_uuid=True),
            existing_nullable=False,
            postgresql_using="tenant_id::text::uuid",
        )

    for table in _CREATED_BY_TABLES:
        op.alter_column(
            table,
            "created_by",
            existing_type=sa.BigInteger(),
            type_=sa.dialects.postgresql.UUID(as_uuid=True),
            existing_nullable=False,
            postgresql_using="created_by::text::uuid",
        )
