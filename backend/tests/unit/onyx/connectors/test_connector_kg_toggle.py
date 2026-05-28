"""Unit tests for KG toggle fields on connector models.

Verifies that kg_processing_enabled and kg_coverage_days are correctly
handled by ConnectorBase, ConnectorUpdateRequest, and ConnectorSnapshot.
"""

from datetime import datetime
from unittest.mock import MagicMock

from onyx.configs.constants import DocumentSource
from onyx.connectors.models import InputType
from onyx.db.enums import AccessType
from onyx.server.documents.models import ConnectorBase
from onyx.server.documents.models import ConnectorSnapshot
from onyx.server.documents.models import ConnectorUpdateRequest


def test_connector_base_defaults_kg_fields() -> None:
    """KG fields should default to disabled when not specified."""
    base = ConnectorBase(
        name="test",
        source=DocumentSource.FILE,
        input_type=InputType.LOAD_STATE,
        connector_specific_config={},
    )
    assert base.kg_processing_enabled is False
    assert base.kg_coverage_days is None


def test_connector_base_accepts_kg_fields() -> None:
    """KG fields should be settable on ConnectorBase."""
    base = ConnectorBase(
        name="test",
        source=DocumentSource.FILE,
        input_type=InputType.LOAD_STATE,
        connector_specific_config={},
        kg_processing_enabled=True,
        kg_coverage_days=90,
    )
    assert base.kg_processing_enabled is True
    assert base.kg_coverage_days == 90


def test_connector_update_request_to_connector_base_preserves_kg_fields() -> None:
    """to_connector_base() must not strip KG fields."""
    request = ConnectorUpdateRequest(
        name="test",
        source=DocumentSource.FILE,
        input_type=InputType.LOAD_STATE,
        connector_specific_config={},
        access_type=AccessType.PUBLIC,
        groups=[],
        kg_processing_enabled=True,
        kg_coverage_days=30,
    )
    base = request.to_connector_base()
    assert base.kg_processing_enabled is True
    assert base.kg_coverage_days == 30


def test_connector_update_request_to_connector_base_defaults() -> None:
    """to_connector_base() should preserve defaults for KG fields."""
    request = ConnectorUpdateRequest(
        name="test",
        source=DocumentSource.FILE,
        input_type=InputType.LOAD_STATE,
        connector_specific_config={},
        access_type=AccessType.PUBLIC,
    )
    base = request.to_connector_base()
    assert base.kg_processing_enabled is False
    assert base.kg_coverage_days is None


def _make_mock_connector(
    kg_processing_enabled: bool = False,
    kg_coverage_days: int | None = None,
) -> MagicMock:
    """Create a mock Connector ORM object with required fields."""
    connector = MagicMock()
    connector.id = 1
    connector.name = "test-connector"
    connector.source = DocumentSource.FILE
    connector.input_type = InputType.LOAD_STATE
    connector.connector_specific_config = {}
    connector.refresh_freq = None
    connector.prune_freq = None
    connector.indexing_start = None
    connector.time_created = datetime(2026, 1, 1)
    connector.time_updated = datetime(2026, 1, 1)
    connector.credentials = []
    connector.kg_processing_enabled = kg_processing_enabled
    connector.kg_coverage_days = kg_coverage_days
    return connector


def test_connector_snapshot_from_db_model_kg_enabled() -> None:
    """from_connector_db_model should map KG fields when enabled."""
    mock = _make_mock_connector(kg_processing_enabled=True, kg_coverage_days=60)
    snapshot = ConnectorSnapshot.from_connector_db_model(mock)
    assert snapshot.kg_processing_enabled is True
    assert snapshot.kg_coverage_days == 60


def test_connector_snapshot_from_db_model_kg_disabled() -> None:
    """from_connector_db_model should map KG fields when disabled."""
    mock = _make_mock_connector(kg_processing_enabled=False, kg_coverage_days=None)
    snapshot = ConnectorSnapshot.from_connector_db_model(mock)
    assert snapshot.kg_processing_enabled is False
    assert snapshot.kg_coverage_days is None


def test_connector_base_model_dump_includes_kg_fields() -> None:
    """model_dump() should include KG fields for API serialization."""
    base = ConnectorBase(
        name="test",
        source=DocumentSource.FILE,
        input_type=InputType.LOAD_STATE,
        connector_specific_config={},
        kg_processing_enabled=True,
        kg_coverage_days=45,
    )
    dumped = base.model_dump()
    assert "kg_processing_enabled" in dumped
    assert dumped["kg_processing_enabled"] is True
    assert "kg_coverage_days" in dumped
    assert dumped["kg_coverage_days"] == 45
