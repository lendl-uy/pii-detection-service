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
    result = db_manager.query_entries({"full_text": "Hello"}, 1)
    assert result is not None
    assert result[0].full_text == "Hello"
    assert result[0].tokens == ["Hello"]
    assert result[0].labels == ["B-NAME"]
    assert result[0].validated_labels == ["B-NAME"]
    assert result[0].for_retrain is True
    session.close()

def test_update(db_manager):
    """Test the update method."""
    session = db_manager.Session()
    try:
        entry = DocumentEntry(full_text="Hello", tokens=["Hello"], labels=["B-NAME"], validated_labels=["O"], for_retrain=True)
        session.add(entry)
        session.commit()

        db_manager.update_entry({"doc_id": entry.doc_id}, {"full_text": "Hello Updated"})

        session.refresh(entry)
        assert entry.full_text == "Hello Updated"

    finally:
        session.close()

def test_query(db_manager):
    """Test the query method."""
    entry = DocumentEntry(full_text="Query Test", tokens=["Test"], labels=["Query"], validated_labels=["Query"], for_retrain=False)
    session = db_manager.Session()
    db_manager.add_entry(entry)
    filter_criteria = {"full_text": "Query Test"}
    result = db_manager.query_entries(filter_criteria, 1)
    assert result[0].full_text == "Query Test"
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