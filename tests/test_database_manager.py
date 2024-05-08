import pytest
from app.infra.database_manager import DatabaseManager
from app.infra.constants import *

@pytest.fixture(scope="module")
def db_manager():
    """Fixture to connect to the database before tests and disconnect afterwards."""
    manager = DatabaseManager(DB_HOST, DB_USER, DB_PASS, DB_NAME)
    manager.connect()
    yield manager
    # Teardown: Clear the database and close connection
    manager.clear(TABLE_NAME)
    manager.disconnect()

def test_insert(db_manager):
    """Test the insert method."""
    assert db_manager.insert(TABLE_NAME, full_text="Hello", tokens=["Hello"], labels=["B-NAME"], validated_labels=["B-NAME"], for_retrain=True) == True
    result = db_manager.query(f"SELECT full_text, tokens, labels, validated_labels, for_retrain FROM {TABLE_NAME}")
    assert result == ("Hello", ["Hello"], ["B-NAME"], ["B-NAME"], True)

def test_update(db_manager):
    """Test the update method."""
    db_manager.insert(TABLE_NAME, full_text="Hello", tokens=["Hello"], labels=["B-NAME"], validated_labels=["O"], for_retrain=True)
    assert db_manager.update(TABLE_NAME, "full_text", "Hello Updated", "full_text", "Hello") == True

    new_full_text = "Hello Updated"
    result = db_manager.query(f"SELECT full_text FROM {TABLE_NAME} WHERE full_text = %s", (new_full_text,))
    assert result == (new_full_text,)

def test_query(db_manager):
    """Test the query method."""
    db_manager.insert(TABLE_NAME, full_text="Query Test", tokens=["Test"], labels=["Query"], validated_labels=["Query"], for_retrain=False)
    result = db_manager.query(f"SELECT full_text FROM {TABLE_NAME} WHERE full_text = %s", ('Query Test',))
    assert result == ('Query Test',)

def test_clear(db_manager):
    """Test the clear method."""
    db_manager.insert(TABLE_NAME, full_text="To Clear", tokens=["Clear"], labels=["Test"], validated_labels=["Test"], for_retrain=False)
    db_manager.clear(TABLE_NAME)
    result = db_manager.query(f"SELECT * FROM {TABLE_NAME}")
    assert result is None