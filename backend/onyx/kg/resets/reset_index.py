from sqlalchemy.orm import Session

from onyx.db.document import reset_all_document_kg_stages
from onyx.db.models import Connector
from onyx.db.models import KGEntity
from onyx.db.models import KGEntityExtractionStaging
from onyx.db.models import KGEntityType
from onyx.db.models import KGRelationship
from onyx.db.models import KGRelationshipExtractionStaging
from onyx.db.models import KGRelationshipType
from onyx.db.models import KGRelationshipTypeExtractionStaging
from onyx.utils.logger import setup_logger

logger = setup_logger()


def reset_full_kg_index__commit(db_session: Session) -> None:
    """
    Resets the knowledge graph index.
    """

    db_session.query(KGRelationship).delete()
    db_session.query(KGRelationshipType).delete()
    db_session.query(KGEntity).delete()
    db_session.query(KGRelationshipExtractionStaging).delete()
    db_session.query(KGEntityExtractionStaging).delete()
    db_session.query(KGRelationshipTypeExtractionStaging).delete()
    # Update all connectors to disable KG processing
    db_session.query(Connector).update({"kg_processing_enabled": False})

    # Only reset grounded entity types
    db_session.query(KGEntityType).filter(
        KGEntityType.grounded_source_name.isnot(None)
    ).update({"active": False})

    reset_all_document_kg_stages(db_session)

    # Wipe Neo4j if enabled
    from onyx.configs.kg_configs import KG_QUERY_BACKEND

    if KG_QUERY_BACKEND == "neo4j":
        try:
            from onyx.db.neo4j_client import get_neo4j_database
            from onyx.db.neo4j_client import get_neo4j_driver

            driver = get_neo4j_driver()
            with driver.session(database=get_neo4j_database()) as session:
                session.run("MATCH (n) DETACH DELETE n")
            logger.info("Neo4j: cleared all nodes on full KG reset")
        except Exception:
            logger.warning("Neo4j cleanup failed during full KG reset")

    db_session.commit()
