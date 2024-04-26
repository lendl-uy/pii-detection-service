import json
import pytest
from app.services.ml_service.constants import BLANK_NER
from app.services.ml_service.predictor import Predictor
from app.infra.object_store_manager import ObjectStoreManager
from app.infra.constants import *

@pytest.fixture(scope="module")
def model():
    # Setup code: load the model before tests
    model_name = BLANK_NER
    # Create an object store manager to pull model from
    s3 = ObjectStoreManager(S3_BUCKET_NAME)
    predictor = Predictor(model_name)
    predictor.get_model(model_name, s3)
    yield predictor
    # Teardown code: delete the model after tests
    predictor.delete_model(model_name)

def test_predict_sample_document_from_test_set(model):
    # Arrange
    with open("test.json") as sample_documents:  # Adjust the path to your test.json
        documents = json.load(sample_documents)
    
    # Assume the test expects at least one document in test.json
    document = documents[0]["full_text"]
    
    # Act
    predictions = model.predict(document, BLANK_NER)
    
    # Assert
    assert isinstance(predictions, list)
    assert len(predictions) > 0  # Add more specific checks based on your prediction format