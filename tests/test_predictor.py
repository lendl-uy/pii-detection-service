import os
import logging
import pytest
from app.services.ml_service.constants import BLANK_NER, PRETRAINED_EN_NER
from app.services.ml_service.predictor import Predictor
from app.infra.object_store_manager import ObjectStoreManager
from app.infra.database_manager import DatabaseManager, DocumentEntry

sample_text = "John Doe, a 35-year-old software engineer, lives at 1234 Maple Drive, Springfield, IL. He moved there in June 2015. You can reach him at his personal email, john.doe@example.com, or his mobile phone, 555-123-4567. John's previous address was 987 Elm Street, Centerville, OH."
sample_tokens = ['John', 'Doe', ',', 'a', '35', '-', 'year', '-', 'old', 'software', 'engineer', ',', 'lives', 'at', '1234', 'Maple', 'Drive', ',', 'Springfield', ',', 'IL', '.', 'He', 'moved', 'there', 'in', 'June', '2015', '.', 'You', 'can', 'reach', 'him', 'at', 'his', 'personal', 'email', ',', 'john', '.', 'doe', '@', 'example', '.', 'com', ',', 'or', 'his', 'mobile', 'phone', ',', '555', '-', '123', '-', '4567', '.', 'John', "'", 's', 'previous', 'address', 'was', '987', 'Elm', 'Street', ',', 'Centerville', ',', 'OH', '.']

logging.basicConfig(level=logging.DEBUG)

@pytest.fixture(scope="module")
def model():
    """
    Fixture to set up the database and predictor before tests and clean up afterwards.
    """
    # Load environment variables
    DB_HOST = os.getenv("DB_HOST")
    DB_USER = os.getenv("DB_USER")
    DB_PASS = os.getenv("DB_PASS")
    DB_NAME = os.getenv("DB_NAME")
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

    db_manager = DatabaseManager(DB_HOST, DB_USER, DB_PASS, DB_NAME)
    s3_manager = ObjectStoreManager(S3_BUCKET_NAME, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)

    predictor = Predictor(PRETRAINED_EN_NER)
    predictor.get_model(PRETRAINED_EN_NER, s3_manager)

    yield db_manager, predictor

    predictor.delete_model(PRETRAINED_EN_NER)
    db_manager.clear_table()

def test_predict_sample_document_from_test_set(model):
    """
    Test that the predictor can predict labels for a sample document and save them to the database.
    """
    db_manager, predictor = model
    session = db_manager.Session()

    try:
        # Insert sample data into the database
        entry = DocumentEntry(full_text=sample_text, tokens=sample_tokens)
        session.add(entry)
        session.commit()

        # Retrieve the first document from the database and predict
        document = session.query(DocumentEntry).first()
        text = document.full_text if document else None
        assert text is not None, "No document retrieved."

        # Make predictions
        predictor.predict(text, PRETRAINED_EN_NER)
        predictor.save_predictions_to_database(session)

        # Check if predictions are saved and match
        assert isinstance(predictor.predictions, list), "Predictions should be a list."

        # Reload the entry to ensure predictions are stored
        session.refresh(entry)
        print(f"\n\nentry.labels = {entry.labels}")
        assert entry.labels == predictor.predictions, "Inserted labels do not match."

    finally:
        session.close()