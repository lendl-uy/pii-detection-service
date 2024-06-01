import pytest
import os
from dotenv import load_dotenv

from app.services.ml_service.constants import DEBERTA_NER, sample_text, sample_tokens
from app.services.ml_service.predictor import Predictor
from app.infra.object_store_manager import ObjectStoreManager
from app.infra.database_manager import DatabaseManager, DocumentEntry

# For local testing only
# Load environment variables from .env file
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

@pytest.fixture(scope="module")
def model():
    db_manager = DatabaseManager(DB_HOST, DB_USER, DB_PASS, DB_NAME)
    s3_manager = ObjectStoreManager(S3_BUCKET_NAME)

    predictor = Predictor(DEBERTA_NER)
    predictor.get_model(s3_manager)

    yield db_manager, predictor

    predictor.delete_model(DEBERTA_NER)
    db_manager.clear_table(DocumentEntry)

def test_predict_sample_document_from_test_set(model):
    db_manager, predictor = model

    # Insert sample data into the database
    entry = DocumentEntry(full_text=sample_text, tokens=sample_tokens)
    db_manager.add_entry(entry)

    # Retrieve the first document from the database and predict
    document = db_manager.query_entries(DocumentEntry, limit=1)[0]
    text = document.full_text if document else None
    assert text is not None, "No document retrieved."

    # Make predictions
    predictor.predict_deberta(text, DEBERTA_NER)
    predictor.save_predictions_to_database(db_manager)

    # Check if predictions are saved and match
    assert isinstance(predictor.predictions, list), "Predictions should be a list."

    # Reload the entry to ensure predictions are stored
    entry = db_manager.query_entries(DocumentEntry, {"full_text": text}, limit=1)[0]

    # print fulltext, tokens, labels, and predictions
    print(f"Full Text: {entry.full_text}")
    print(f"Tokens: {entry.tokens}")
    print(f"Labels: {entry.labels}")
    print(f"Predictions: {predictor.predictions}")

    assert entry.labels == predictor.predictions, "Inserted labels do not match."
