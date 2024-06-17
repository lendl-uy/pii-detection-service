import pytest
import os
from dotenv import load_dotenv

from app.infra.database_manager import DatabaseManager, DocumentEntry
from app.infra.object_store_manager import ObjectStoreManager
from app.services.ml_service.constants import *
from app.services.ml_service.model_retrainer import ModelRetrainer

# For local testing only
# Load environment variables from .env filex
load_dotenv()

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

@pytest.fixture(scope="function")
def infra_manager():
    s3_manager = ObjectStoreManager(S3_BUCKET_NAME)
    yield s3_manager

def test_model_retrainer_get_dataset(infra_manager):
    s3_manager = infra_manager

    texts = [sample_text_1 for i in range(10)]
    tokens = [sample_tokens_1 for i in range(10)]
    labels = [sample_labels_1 for i in range(10)]

    # Process the data correctly
    model_retrainer = ModelRetrainer(SPACY_BLANK_NER)
    texts_train, tokens_train, labels_train, texts_test, tokens_test, labels_test = model_retrainer.split_dataset(texts, tokens, labels)
    model_retrainer.get_model(s3_manager)

    model_retrainer.retrain(texts_train, tokens_train, labels_train, 1)
    model_retrainer.evaluate(texts_test, tokens_test, labels_test)

    model_retrainer.save_and_upload_model(s3_manager)