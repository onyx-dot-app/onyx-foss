"""fix_kg_entity_name_trigger_for_person

For PERSON-typed entities the document_id points to a CV file, but the entity's
identity is the person's real name — NOT the document filename.  The previous
trigger unconditionally replaced the entity name with the document's semantic_id
whenever document_id was set, which caused PERSON entities extracted from CVs to
end up named "cv_adam_adam.pdf" instead of "Adam Adam".

This migration updates both trigger functions to skip the name-override for
PERSON entity types.

Revision ID: dbc8051006e2
Revises: 503883791c39
Create Date: 2026-04-13 00:00:00.000000

"""

from alembic import op
from sqlalchemy import text
from sqlalchemy.orm import Session
from shared_configs.configs import POSTGRES_DEFAULT_SCHEMA

# revision identifiers, used by Alembic.
revision = "dbc8051006e2"
down_revision = "503883791c39"
branch_labels = None
depends_on = None


def _get_tenant_contextvar(session: Session) -> str:
    current_tenant = session.execute(text("SELECT current_schema()")).scalar()
    if isinstance(current_tenant, str):
        return current_tenant
    raise ValueError("Current tenant is not a string")


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    tenant_id = _get_tenant_contextvar(session)

    alphanum_pattern = r"[^a-z0-9]+"
    truncate_length = 1000

    # ------------------------------------------------------------------
    # update_kg_entity_name
    # Only use the document's semantic_id as the entity name when the
    # entity is NOT a PERSON (i.e. for calls, tickets, issues, etc.).
    # For PERSON entities (CVs) the real name comes from the extraction.
    # ------------------------------------------------------------------
    function = "update_kg_entity_name"
    op.execute(
        text(
            f"""
            CREATE OR REPLACE FUNCTION "{tenant_id}".{function}()
            RETURNS TRIGGER AS $$
            DECLARE
                name text;
                cleaned_name text;
            BEGIN
                -- Only rename for document-type entities where the entity IS
                -- the document (JIRA tickets, calls, PRs, etc.). All other
                -- entity types (CV-extracted skills, companies, etc.) keep
                -- their real extracted name even when document_id is set.
                IF NEW.document_id IS NOT NULL AND NEW.entity_type_id_name IN (
                    'LINEAR', 'JIRA', 'GITHUB_PR', 'GITHUB_ISSUE',
                    'FIREFLIES', 'ACCOUNT', 'OPPORTUNITY'
                ) THEN
                    SELECT lower(semantic_id) INTO name
                    FROM "{tenant_id}".document
                    WHERE id = NEW.document_id;
                ELSE
                    name = lower(NEW.name);
                END IF;

                -- Clean name and truncate if too long
                cleaned_name = regexp_replace(
                    name,
                    '{alphanum_pattern}', '', 'g'
                );
                IF length(cleaned_name) > {truncate_length} THEN
                    cleaned_name = left(cleaned_name, {truncate_length});
                END IF;

                -- Set name and name trigrams
                NEW.name = name;
                NEW.name_trigrams = {POSTGRES_DEFAULT_SCHEMA}.show_trgm(cleaned_name);
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            """
        )
    )
    trigger = f"{function}_trigger"
    op.execute(f'DROP TRIGGER IF EXISTS {trigger} ON "{tenant_id}".kg_entity')
    op.execute(
        f"""
        CREATE TRIGGER {trigger}
            BEFORE INSERT OR UPDATE OF name
            ON "{tenant_id}".kg_entity
            FOR EACH ROW
            EXECUTE FUNCTION "{tenant_id}".{function}();
        """
    )

    # ------------------------------------------------------------------
    # update_kg_entity_name_from_doc
    # When a document's semantic_id changes, propagate the new name to
    # kg_entity rows that reference it — but NOT for PERSON entities,
    # whose names are real person names that must not be clobbered.
    # ------------------------------------------------------------------
    function = "update_kg_entity_name_from_doc"
    op.execute(
        text(
            f"""
            CREATE OR REPLACE FUNCTION "{tenant_id}".{function}()
            RETURNS TRIGGER AS $$
            DECLARE
                doc_name text;
                cleaned_name text;
            BEGIN
                doc_name = lower(NEW.semantic_id);

                -- Clean name and truncate if too long
                cleaned_name = regexp_replace(
                    doc_name,
                    '{alphanum_pattern}', '', 'g'
                );
                IF length(cleaned_name) > {truncate_length} THEN
                    cleaned_name = left(cleaned_name, {truncate_length});
                END IF;

                -- Only propagate the document name to document-type entities
                -- (where the entity IS the document). CV-extracted entities
                -- keep their real names.
                UPDATE "{tenant_id}".kg_entity
                SET
                    name = doc_name,
                    name_trigrams = {POSTGRES_DEFAULT_SCHEMA}.show_trgm(cleaned_name)
                WHERE document_id = NEW.id
                  AND entity_type_id_name IN (
                    'LINEAR', 'JIRA', 'GITHUB_PR', 'GITHUB_ISSUE',
                    'FIREFLIES', 'ACCOUNT', 'OPPORTUNITY'
                  );
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            """
        )
    )
    trigger = f"{function}_trigger"
    op.execute(f'DROP TRIGGER IF EXISTS {trigger} ON "{tenant_id}".document')
    op.execute(
        f"""
        CREATE TRIGGER {trigger}
            AFTER UPDATE OF semantic_id
            ON "{tenant_id}".document
            FOR EACH ROW
            EXECUTE FUNCTION "{tenant_id}".{function}();
        """
    )


def downgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    tenant_id = _get_tenant_contextvar(session)

    alphanum_pattern = r"[^a-z0-9]+"
    truncate_length = 1000

    function = "update_kg_entity_name"
    op.execute(
        text(
            f"""
            CREATE OR REPLACE FUNCTION "{tenant_id}".{function}()
            RETURNS TRIGGER AS $$
            DECLARE
                name text;
                cleaned_name text;
            BEGIN
                IF NEW.document_id IS NOT NULL THEN
                    SELECT lower(semantic_id) INTO name
                    FROM "{tenant_id}".document
                    WHERE id = NEW.document_id;
                ELSE
                    name = lower(NEW.name);
                END IF;

                cleaned_name = regexp_replace(
                    name,
                    '{alphanum_pattern}', '', 'g'
                );
                IF length(cleaned_name) > {truncate_length} THEN
                    cleaned_name = left(cleaned_name, {truncate_length});
                END IF;

                NEW.name = name;
                NEW.name_trigrams = {POSTGRES_DEFAULT_SCHEMA}.show_trgm(cleaned_name);
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            """
        )
    )
    trigger = f"{function}_trigger"
    op.execute(f'DROP TRIGGER IF EXISTS {trigger} ON "{tenant_id}".kg_entity')
    op.execute(
        f"""
        CREATE TRIGGER {trigger}
            BEFORE INSERT OR UPDATE OF name
            ON "{tenant_id}".kg_entity
            FOR EACH ROW
            EXECUTE FUNCTION "{tenant_id}".{function}();
        """
    )

    function = "update_kg_entity_name_from_doc"
    op.execute(
        text(
            f"""
            CREATE OR REPLACE FUNCTION "{tenant_id}".{function}()
            RETURNS TRIGGER AS $$
            DECLARE
                doc_name text;
                cleaned_name text;
            BEGIN
                doc_name = lower(NEW.semantic_id);

                cleaned_name = regexp_replace(
                    doc_name,
                    '{alphanum_pattern}', '', 'g'
                );
                IF length(cleaned_name) > {truncate_length} THEN
                    cleaned_name = left(cleaned_name, {truncate_length});
                END IF;

                UPDATE "{tenant_id}".kg_entity
                SET
                    name = doc_name,
                    name_trigrams = {POSTGRES_DEFAULT_SCHEMA}.show_trgm(cleaned_name)
                WHERE document_id = NEW.id;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            """
        )
    )
    trigger = f"{function}_trigger"
    op.execute(f'DROP TRIGGER IF EXISTS {trigger} ON "{tenant_id}".document')
    op.execute(
        f"""
        CREATE TRIGGER {trigger}
            AFTER UPDATE OF semantic_id
            ON "{tenant_id}".document
            FOR EACH ROW
            EXECUTE FUNCTION "{tenant_id}".{function}();
        """
    )
