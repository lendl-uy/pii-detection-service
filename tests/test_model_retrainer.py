import pytest
from app.infra.database_manager import DatabaseManager
from app.infra.object_store_manager import ObjectStoreManager
from app.infra.constants import *
from app.services.ml_service.constants import BLANK_NER
from app.services.ml_service.model_retrainer import ModelRetrainer

sample_text_1 = "Alice Johnson called from 212-555-1234. Her email is alice.j@example.com."
sample_tokens_1 = ["Alice", "Johnson", "called", "from", "212-555-1234", ".", "Her", "email", "is", "alice.j@example.com", "."]
sample_labels_1 = ["B-NAME", "I-NAME", "O", "O", "B-PHONE", "O", "O", "O", "O", "B-EMAIL", "O"]

sample_text_2 = "Dr. Robert Smith will see you now. His office number at 456 Elm St is 415-555-9876."
sample_tokens_2 = ["Dr.", "Robert", "Smith", "will", "see", "you", "now", ".", "His", "office", "number", "at", "456", "Elm", "St", "is", "415-555-9876", "."]
sample_labels_2 = ["O", "B-NAME", "I-NAME", "O", "O", "O", "O", "O", "O", "O", "O", "O", "B-ADDRESS", "I-ADDRESS", "I-ADDRESS", "O", "B-PHONE", "O"]

@pytest.fixture(scope="function")
def infra_manager():
    # Create a database manager to connect to the database
    db = DatabaseManager(DB_HOST, DB_USER, DB_PASS, DB_NAME)
    db.connect()

    # Create an object store manager to pull model from
    s3 = ObjectStoreManager(S3_BUCKET_NAME)

    yield db, s3

    db.clear(TABLE_NAME)
    db.disconnect()

def test_model_retrainer_get_dataset(infra_manager):

    db, s3 = infra_manager

    for i in range(5):
        db.insert(TABLE_NAME, full_text=sample_text_1, tokens=sample_tokens_1, labels=sample_labels_1, for_retrain=True)
        db.insert(TABLE_NAME, full_text=sample_text_2, tokens=sample_tokens_2, labels=sample_labels_2, for_retrain=True)

    model_retrainer = ModelRetrainer(BLANK_NER)
    texts, tokens, labels = model_retrainer.get_dataset(db)

    texts_train, tokens_train, labels_train, texts_test, tokens_test, labels_test = model_retrainer.split_dataset(texts, tokens, labels)
    model_retrainer.get_model(s3)

    model_retrainer.retrain(texts_train, tokens_train, labels_train, 1)
    model_retrainer.evaluate(texts_test, tokens_test, labels_test)

    model_retrainer.save_and_upload_model(s3)

