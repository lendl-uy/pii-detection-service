import pytest
from app.services.ml_service.constants import BLANK_NER, PRETRAINED_EN_NER
from app.services.ml_service.predictor import Predictor
from app.infra.object_store_manager import ObjectStoreManager
from app.infra.database_manager import DatabaseManager
from app.infra.constants import *

sample_text = "John Doe, a 35-year-old software engineer, lives at 1234 Maple Drive, Springfield, IL. He moved there in June 2015. You can reach him at his personal email, john.doe@example.com, or his mobile phone, 555-123-4567. John's previous address was 987 Elm Street, Centerville, OH."
sample_tokens = ['John', 'Doe', ',', 'a', '35', '-', 'year', '-', 'old', 'software', 'engineer', ',', 'lives', 'at', '1234', 'Maple', 'Drive', ',', 'Springfield', ',', 'IL', '.', 'He', 'moved', 'there', 'in', 'June', '2015', '.', 'You', 'can', 'reach', 'him', 'at', 'his', 'personal', 'email', ',', 'john', '.', 'doe', '@', 'example', '.', 'com', ',', 'or', 'his', 'mobile', 'phone', ',', '555', '-', '123', '-', '4567', '.', 'John', "'", 's', 'previous', 'address', 'was', '987', 'Elm', 'Street', ',', 'Centerville', ',', 'OH', '.']

@pytest.fixture(scope="module")
def model():
    # Setup code: load the model before tests
    model_name = PRETRAINED_EN_NER

    # Create an object store manager to pull model from
    s3 = ObjectStoreManager(S3_BUCKET_NAME)
    db = DatabaseManager(DB_HOST, DB_USER, DB_PASS, DB_NAME)
    db.connect()

    predictor = Predictor(model_name)
    predictor.get_model(model_name, s3)

    yield db, predictor

    # Teardown code: delete the model after tests
    predictor.delete_model(model_name)
    db.disconnect()

def test_predict_sample_document_from_test_set(model):
    db, predictor = model

    db.insert(TABLE_NAME, full_text=sample_text, tokens=sample_tokens)

    # Arrange
    query = """
                    SELECT full_text FROM document_table LIMIT 1
                """
    document = db.query(query)
    text = document[0]

    # Act
    predictor.predict(text, PRETRAINED_EN_NER)
    predictor.save_predictions_to_database(db)

    # Assert
    assert isinstance(predictor.predictions, list)

    # Verify that the data was inserted correctly
    query = """
                SELECT labels FROM document_table LIMIT 1
            """
    inserted_data = db.query(query, (text,))
    print(inserted_data)
    assert inserted_data is not None, "No data was inserted."
    assert inserted_data[0] == predictor.predictions, "Inserted labels do not match."