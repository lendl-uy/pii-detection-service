import pytest
from app.infra.database_manager import DatabaseManager
from app.infra.object_store_manager import ObjectStoreManager
from app.infra.constants import *
from app.services.ml_service.constants import BLANK_NER
from app.services.ml_service.model_retrainer import ModelRetrainer

# For database testing
SAMPLE_ESSAY_WITH_LABELS = "sample_input_with_labels.json"

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

# def test_retrain_model_with_first_five_rows(db_manager):
#
#     model_retrainer = ModelRetrainer(BLANK_NER)
#     model_retrainer.get_dataset(db_manager)

def test_model_retrainer_get_dataset(infra_manager):

    db, s3 = infra_manager

    model_retrainer = ModelRetrainer(BLANK_NER)
    texts, tokens, labels = model_retrainer.get_dataset(db)
