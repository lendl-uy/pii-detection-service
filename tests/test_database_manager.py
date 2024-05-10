import pytest
from app.infra.database_manager import DatabaseManager, DocumentEntry
from app.infra.constants import DB_HOST, DB_USER, DB_PASS, DB_NAME

@pytest.fixture(scope="module")
def db_manager():
    """Fixture to connect to the database before tests and disconnect afterwards."""
    manager = DatabaseManager(DB_HOST, DB_USER, DB_PASS, DB_NAME)
    yield manager
    # Teardown: Clear the database
    manager.clear_table()

def test_insert(db_manager):
    """Test the insert method."""
    entry = DocumentEntry(full_text="Hello", tokens=["Hello"], labels=["B-NAME"], validated_labels=["B-NAME"], for_retrain=True)
    session = db_manager.Session()
    db_manager.add_entry(entry)
    result = session.query(DocumentEntry).filter(DocumentEntry.full_text == "Hello").first()
    assert result is not None
    assert result.full_text == "Hello"
    assert result.tokens == ["Hello"]
    assert result.labels == ["B-NAME"]
    assert result.validated_labels == ["B-NAME"]
    assert result.for_retrain is True
    session.close()

def test_update(db_manager):
    """Test the update method."""
    session = db_manager.Session()
    try:
        entry = DocumentEntry(full_text="Hello", tokens=["Hello"], labels=["B-NAME"], validated_labels=["O"], for_retrain=True)
        session.add(entry)
        session.commit() # Ensures the entry is persisted and session is still valid

        db_manager.update_entry(entry.doc_id, {"full_text": "Hello Updated"})

        session.refresh(entry)  # Refresh the entry to get updated values from the database
        assert entry.full_text == "Hello Updated"

    finally:
        session.close()

def test_query(db_manager):
    """Test the query method."""
    entry = DocumentEntry(full_text="Query Test", tokens=["Test"], labels=["Query"], validated_labels=["Query"], for_retrain=False)
    session = db_manager.Session()
    db_manager.add_entry(entry)
    result = session.query(DocumentEntry).filter(DocumentEntry.full_text == "Query Test").first()
    assert result is not DocumentEntry
    assert result.full_text == "Query Test"
    session.close()

def test_clear(db_manager):
    """Test the clear method."""
    entry = DocumentEntry(full_text="To Clear", tokens=["Clear"], labels=["Test"], validated_labels=["Test"], for_retrain=False)
    session = db_manager.Session()
    db_manager.add_entry(entry)
    db_manager.clear_table()
    result = session.query(DocumentEntry).all()
    assert len(result) == 0
    session.close()