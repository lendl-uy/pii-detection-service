from flask import Flask, request, jsonify
import requests
import logging
import time

from app.infra.database_manager import DatabaseManager, DocumentEntry
from app.infra.constants import DB_HOST, DB_USER, DB_PASS, DB_NAME, S3_BUCKET_NAME
from app.infra.object_store_manager import ObjectStoreManager
from app.services.ml_service.predictor import Predictor
from app.services.ml_service.model_retrainer import ModelRetrainer
from app.services.ml_service.constants import PRETRAINED_EN_NER

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route("/predict", methods=["POST"])
def predict():
    # Instantiate connections to the database and the object store
    db_manager = DatabaseManager(DB_HOST, DB_USER, DB_PASS, DB_NAME)
    s3_manager = ObjectStoreManager(S3_BUCKET_NAME)

    # Instantiate the predictor
    logger.info("Pulling the latest model")
    predictor = Predictor(PRETRAINED_EN_NER)
    predictor.get_model(PRETRAINED_EN_NER, s3_manager)

    # Retrieve the document to be predicted with ID specified by the
    # preprocessor endpoint
    logger.info("Retrieving the document")
    entry = db_manager.query_entries(limit=1)
    full_text = entry[0].full_text if entry else None

    # Perform predictions on the input full text
    logger.info("Predicting PIIs from the given full text")
    start_time = time.time()
    predictor.predict(full_text, PRETRAINED_EN_NER)
    runtime = str(time.time() - start_time) + " s"

    db_manager.update_entry({"doc_id": entry[0].doc_id}, {"labels": predictor.predictions})
    entry = db_manager.query_entries({"doc_id": entry[0].doc_id}, 1)
    if entry:
        entry[0].labels = predictor.predictions
        requests.post("http://127.0.0.1:5000/ml_response_handler")
        return {"status": "SUCCESS", "document_id": entry[0].doc_id, "runtime": runtime}, 200
    else:
        logger.info("Document not found in the database.")
        return {"status": "FAILED"}, 400

@app.route("/retrain", methods=["POST"])
def retrain():
    logger.info("Model re-training endpoint!")
    db_manager = DatabaseManager(DB_HOST, DB_USER, DB_PASS, DB_NAME)
    s3_manager = ObjectStoreManager(S3_BUCKET_NAME)

    # Retrieve data for training
    entries = db_manager.query_entries({"for_retrain": True}, limit=100)
    # doc_ids = [entry.doc_id for entry in entries]
    # doc_ids.sort()
    if len(entries) < 1:
        return {"status": "Failed", "message": {"Insufficient dataset size for re-training"}}, 200
    texts = [entry.full_text for entry in entries]
    tokens = [entry.tokens for entry in entries]
    labels = [entry.labels for entry in entries]

    # Process the data correctly
    model_retrainer = ModelRetrainer(PRETRAINED_EN_NER)
    texts_train, tokens_train, labels_train, texts_test, tokens_test, labels_test = model_retrainer.split_dataset(texts,
                                                                                                                  tokens,
                                                                                                                  labels)
    model_retrainer.get_model(s3_manager)

    start_time = time.time()
    model_retrainer.retrain(texts_train, tokens_train, labels_train, 1)
    runtime = str(time.time() - start_time) + " s"
    model_retrainer.evaluate(texts_test, tokens_test, labels_test)
    db_manager.update_entry({"for_retrain": True}, {"for_retrain": False})

    return {"status": "Success", "runtime": runtime}, 200

if __name__ == "__main__":
    app.run(debug=True, port=5001)