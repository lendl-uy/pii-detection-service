import pytest
from app.services.ml_service.constants import BLANK_NER, PRETRAINED_EN_NER, sample_text, sample_tokens
from app.services.ml_service.predictor import Predictor
from app.infra.object_store_manager import ObjectStoreManager
from app.infra.database_manager import DatabaseManager, DocumentEntry
from app.infra.constants import *

@pytest.fixture(scope="module")
def model():
    db_manager = DatabaseManager(DB_HOST, DB_USER, DB_PASS, DB_NAME)
    s3_manager = ObjectStoreManager(S3_BUCKET_NAME)

    predictor = Predictor(PRETRAINED_EN_NER)
    predictor.get_model(PRETRAINED_EN_NER, s3_manager)

    yield db_manager, predictor

    predictor.delete_model(PRETRAINED_EN_NER)
    db_manager.clear_table()

def test_predict_sample_document_from_test_set(model):
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

        assert entry.labels == predictor.predictions, "Inserted labels do not match."

    finally:
        session.close()