import os
import pytest
from app.infra.database_manager import DatabaseManager
from app.services.backend_service.preprocessor import Preprocessor
from app.infra.object_store_manager import ObjectStoreManager
from app.infra.constants import *

# For database testing
SAMPLE_ESSAY_NO_LABELS = "sample_input.json"
SAMPLE_ESSAY_WITH_LABELS = "sample_input_with_labels.json"

@pytest.fixture(scope="function")
def db_manager():
    db = DatabaseManager(DB_HOST, DB_USER, DB_PASS, DB_NAME)
    db.connect()
    yield db
    # db.clear(TABLE_NAME)
    db.disconnect()

def test_ingest_full_text_and_tokens_to_database(db_manager):
    object_store_manager = ObjectStoreManager(S3_BUCKET_NAME)

    # Make sure the sample essay file is available
    if not os.path.exists(SAMPLE_ESSAY_NO_LABELS):
        object_store_manager.download(f"datasets/{SAMPLE_ESSAY_NO_LABELS}", SAMPLE_ESSAY_NO_LABELS)

    # Assume the file download was successful
    assert os.path.exists(SAMPLE_ESSAY_NO_LABELS)

    # Open the JSON file
    with open(SAMPLE_ESSAY_NO_LABELS, "r") as sample_essay:
        preprocessor = Preprocessor()

        # Obtain then preprocess data
        full_text = preprocessor.parse_json("sample_pii_data", sample_essay)
        tokens = preprocessor.tokenize(full_text)

        # Insert data into the database
        insert_success = preprocessor.ingest_to_database(db_manager=db_manager,
                                                         full_text=full_text,
                                                         tokens=tokens)

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