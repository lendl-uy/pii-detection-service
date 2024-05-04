import os
import pytest
from app.infra.database_manager import DatabaseManager
from app.services.backend_service.preprocessor import Preprocessor
from app.infra.object_store_manager import ObjectStoreManager
from app.infra.constants import *

@pytest.fixture(scope="function")
def db_manager():
    db = DatabaseManager(DB_HOST, DB_USER, DB_PASS, DB_NAME)
    db.connect()
    yield db
    db.clear(TABLE_NAME)
    db.disconnect()

def test_from_json_to_insertion_in_database(db_manager):
    object_store_manager = ObjectStoreManager(S3_BUCKET_NAME)

    # Make sure the sample essay file is available
    if not os.path.exists(PATH_TO_SAMPLE_ESSAY):
        object_store_manager.download("datasets/sample_input.json", PATH_TO_SAMPLE_ESSAY)

    # Assume the file download was successful
    assert os.path.exists(PATH_TO_SAMPLE_ESSAY)

    # Open the JSON file
    with open(PATH_TO_SAMPLE_ESSAY, "r") as sample_essay:
        preprocessor = Preprocessor()

        # Obtain then preprocess data
        full_text = preprocessor.parse_json(sample_essay)
        tokens = preprocessor.tokenize(full_text)

        # Insert data into the database
        insert_success = db_manager.insert(TABLE_NAME, full_text, tokens)

        # Check if the insertion was successful
        assert insert_success == True, "Data insertion failed."

        # Verify that the data was inserted correctly
        query = """
            SELECT full_text, tokens FROM document_table WHERE full_text = %s LIMIT 1
        """
        inserted_data = db_manager.query(query, (full_text,))
        assert inserted_data is not None, "No data was inserted."
        assert inserted_data[0] == full_text, "Inserted full text does not match."
        assert inserted_data[1] == tokens, "Inserted tokens do not match."