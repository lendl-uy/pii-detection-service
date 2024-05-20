import os
import pytest
from dotenv import load_dotenv

from app.infra.database_manager import DatabaseManager, DocumentEntry
from app.services.backend_service.preprocessor import Preprocessor
from app.infra.object_store_manager import ObjectStoreManager

# For local testing only
# Load environment variables from .env file
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
SAMPLE_ESSAY_NO_LABELS = os.getenv("SAMPLE_ESSAY_NO_LABELS")
SAMPLE_ESSAY_WITH_LABELS = os.getenv("SAMPLE_ESSAY_WITH_LABELS")

@pytest.fixture(scope="function")
def db_manager():
    manager = DatabaseManager(DB_HOST, DB_USER, DB_PASS, DB_NAME)
    yield manager
    manager.clear_table()

def test_ingest_full_text_and_tokens_to_database(db_manager):
    print("Current Working Directory:", os.getcwd())

    object_store_manager = ObjectStoreManager(S3_BUCKET_NAME, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)

    # Ensure the sample essay file is available
    sample_file_path = f"datasets/{SAMPLE_ESSAY_NO_LABELS}"
    if not os.path.exists(sample_file_path):
        object_store_manager.download(sample_file_path, SAMPLE_ESSAY_NO_LABELS)

    assert os.path.exists(SAMPLE_ESSAY_NO_LABELS), "Sample essay file not downloaded correctly."

    # Open and process the JSON file
    with open(SAMPLE_ESSAY_NO_LABELS, "r") as sample_essay:
        preprocessor = Preprocessor()
        full_text = preprocessor.parse_json("sample_pii_data", sample_essay)
        tokens = preprocessor.tokenize(full_text)

        # Create and insert a new data entry
        entry = DocumentEntry(full_text=full_text, tokens=tokens)
        with db_manager.Session() as session:
            session.add(entry)
            session.commit()

            # Verify that the data was inserted correctly
            inserted_entry = session.query(DocumentEntry).filter(DocumentEntry.full_text == full_text).first()
            assert inserted_entry is not None, "No data was inserted."
            assert inserted_entry.full_text == full_text, "Inserted full text does not match."
            assert inserted_entry.tokens == tokens, "Inserted tokens do not match."