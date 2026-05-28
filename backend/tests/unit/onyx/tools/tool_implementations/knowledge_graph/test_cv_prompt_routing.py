"""TDD tests for routing file-connector docs to CV prompt via metadata tag.
Written BEFORE implementation — these should fail initially, then pass.
"""

import sys
from unittest.mock import MagicMock

if "onyx.db.entities" not in sys.modules:
    sys.modules["onyx.db.entities"] = MagicMock()


def test_kg_doc_type_constant_exists() -> None:
    """A constant for the metadata tag key should exist."""
    from onyx.kg.utils.extraction_utils import KG_DOC_TYPE_METADATA_KEY

    assert KG_DOC_TYPE_METADATA_KEY == "kg_doc_type"


def test_kg_doc_type_cv_value_exists() -> None:
    """A constant for the CV value should exist."""
    from onyx.kg.utils.extraction_utils import KG_DOC_TYPE_CV

    assert KG_DOC_TYPE_CV == "cv"


def test_is_cv_document_true_when_tagged() -> None:
    """is_cv_document should return True when metadata has kg_doc_type=cv."""
    from onyx.kg.models import KGChunkFormat
    from onyx.kg.utils.extraction_utils import is_cv_document

    chunks = [
        KGChunkFormat(
            document_id="doc1",
            chunk_id=0,
            title="John Doe CV",
            content="Some CV content",
            primary_owners=[],
            secondary_owners=[],
            source_type="file",
            metadata={"kg_doc_type": "cv"},
        )
    ]
    assert is_cv_document(chunks) is True


def test_is_cv_document_false_when_not_tagged() -> None:
    """is_cv_document should return False when no tag present."""
    from onyx.kg.models import KGChunkFormat
    from onyx.kg.utils.extraction_utils import is_cv_document

    chunks = [
        KGChunkFormat(
            document_id="doc1",
            chunk_id=0,
            title="Some doc",
            content="Some content",
            primary_owners=[],
            secondary_owners=[],
            source_type="file",
            metadata={"other_key": "other_value"},
        )
    ]
    assert is_cv_document(chunks) is False


def test_is_cv_document_false_when_no_metadata() -> None:
    """is_cv_document should return False when metadata is None."""
    from onyx.kg.models import KGChunkFormat
    from onyx.kg.utils.extraction_utils import is_cv_document

    chunks = [
        KGChunkFormat(
            document_id="doc1",
            chunk_id=0,
            title="Some doc",
            content="Some content",
            primary_owners=[],
            secondary_owners=[],
            source_type="file",
            metadata=None,
        )
    ]
    assert is_cv_document(chunks) is False


def test_is_cv_document_checks_any_chunk() -> None:
    """If any chunk in the batch has the tag, it's a CV document."""
    from onyx.kg.models import KGChunkFormat
    from onyx.kg.utils.extraction_utils import is_cv_document

    chunks = [
        KGChunkFormat(
            document_id="doc1",
            chunk_id=0,
            title="page1",
            content="content",
            primary_owners=[],
            secondary_owners=[],
            source_type="file",
            metadata=None,
        ),
        KGChunkFormat(
            document_id="doc1",
            chunk_id=1,
            title="page2",
            content="content",
            primary_owners=[],
            secondary_owners=[],
            source_type="file",
            metadata={"kg_doc_type": "cv"},
        ),
    ]
    assert is_cv_document(chunks) is True
