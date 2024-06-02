import requests
import logging
import time
import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from app.infra.database_manager import DatabaseManager, DocumentEntry, ModelEntry
from app.infra.object_store_manager import ObjectStoreManager
from app.services.ml_service.predictor import Predictor
from app.services.ml_service.model_retrainer import ModelRetrainer
from app.services.ml_service.constants import DEBERTA_NER, ROW_COUNT_THRESHOLD_FOR_RETRAINING

# For local testing only
# Load environment variables from .env file
load_dotenv()

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
BACKEND_SERVICE_HOST = os.getenv("BACKEND_SERVICE_HOST")

# Database configuration
DB_CONFIG = {
    "db_host": os.getenv("DB_HOST"),
    "db_user": os.getenv("DB_USER"),
    "db_pass": os.getenv("DB_PASS"),
    "db_name": os.getenv("DB_NAME")
}

# Object store configuration
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

# Instantiate Flask application
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Instantiate connections to the database and the object store
db_manager = DatabaseManager(**DB_CONFIG)
s3_manager = ObjectStoreManager(S3_BUCKET_NAME)

@app.route("/predict", methods=["POST"])
def predict():
    data = request.json
    doc_id = data.get("doc_id")

    if not doc_id:
        return jsonify({"status": "FAILED", "message": "No document ID provided."}), 400

    # Retrieve the document to be predicted with ID specified by the preprocessor endpoint
    logger.info("Retrieving the document")
    entry = db_manager.query_entries(DocumentEntry, {"doc_id": doc_id}, limit=1)
    if not entry:
        return jsonify({"status": "FAILED", "message": "Document not found."}), 404
    full_text = entry[0].full_text

    # Instantiate the predictor
    logger.info("Pulling the latest model")
    # predictor = Predictor(SPACY_PRETRAINED_EN_NER)
    predictor = Predictor(DEBERTA_NER)
    predictor.get_model(s3_manager)

    if not full_text:
        logger.info("No document found for prediction.")
        return {"status": "FAILED", "message": "Document not found."}, 400

    # Perform predictions on the input full text
    logger.info("Predicting PIIs from the given full text")
    start_time = time.time()
    # predictor.predict(full_text, SPACY_PRETRAINED_EN_NER) # Use SpaCy NER
    predictor.predict_deberta(full_text, DEBERTA_NER) # Use DeBERTa
    logger.info(f"predictions = {predictor.predictions}")
    logger.info("Done predicting PIIs")
    runtime = time.time() - start_time

    # Update the database with predictions
    if entry:
        db_manager.update_entry(DocumentEntry,
                                {"doc_id": entry[0].doc_id},
                                {"labels": predictor.predictions,
                                           "tokens": predictor.tokens})
        updated_entry = db_manager.query_entries(DocumentEntry,
                                                 {"doc_id": entry[0].doc_id},
                                                 1)[0]

        # Construct the data to send to the backend
        predictor_response = {
            "document_id": updated_entry.doc_id,
            "runtime": f"{runtime:.2f} s"
        }
        model_entry = ModelEntry(doc_id=entry[0].doc_id, model_name=DEBERTA_NER, runtime=runtime)
        _ = db_manager.add_entry(model_entry)

        # Send predictions to the backend service
        headers = {"Content-Type": "application/json"}
        response = requests.post(f"http://{BACKEND_SERVICE_HOST}:8000/retrieve-predictions", json=predictor_response, headers=headers)
        if response.status_code == 200:
            return {"status": "SUCCESS", "document_id": updated_entry.doc_id, "runtime": f"{runtime:.2f} s"}, 200
        else:
            logger.error("Failed to send data to backend service.")
            return {"status": "FAILED", "message": "Error sending data to backend service."}, 500
    else:
        logger.info("Document not found in the database after update.")
        return {"status": "FAILED", "message": "Document not updated correctly."}, 400


@app.route("/retrain", methods=["POST"])
def retrain():
    logger.info("Initiating model re-training process.")
    try:
        entries = fetch_entries_for_retraining()
        if not entries:
            return jsonify({"status": "Failed", "message": "Insufficient dataset size for re-training"}), 200

        texts, tokens, labels = extract_data(entries)
        model_retrainer = initialize_model_retrainer()
        if not model_retrainer:
            return jsonify({"status": "Failed", "message": "Failed to initialize model retrainer"}), 500

        trained_model, runtime = perform_retraining(model_retrainer, texts, tokens, labels)
        f5_score = evaluate_model(model_retrainer, texts, tokens, labels)
        update_retrain_flag(entries)

        return jsonify({
            "status": "Success",
            "runtime": f"{runtime:.2f} s",
            "evaluation": f5_score
        }), 200
    except Exception as e:
        logger.error(f"Error during re-training: {e}")
        return jsonify({"status": "Failed", "message": str(e)}), 500

def fetch_entries_for_retraining():
    entries = db_manager.query_entries(DocumentEntry,
                                       {"for_retrain": True},
                                       limit=ROW_COUNT_THRESHOLD_FOR_RETRAINING)
    if len(entries) < 3:
        logger.warning("Insufficient data for re-training.")
        return None
    return entries

def extract_data(entries):
    texts = [entry.full_text for entry in entries]
    tokens = [entry.tokens for entry in entries]
    labels = [entry.labels for entry in entries]
    return texts, tokens, labels

def initialize_model_retrainer():
    try:
        # model_retrainer = ModelRetrainer(SPACY_PRETRAINED_EN_NER)
        model_retrainer = ModelRetrainer(DEBERTA_NER)
        model_retrainer.get_model(s3_manager)
        return model_retrainer
    except Exception as e:
        logger.error(f"Failed to initialize model retrainer: {e}")
        return None

def perform_retraining(model_retrainer, texts, tokens, labels):
    start_time = time.time()
    model_retrainer.retrain(texts, tokens, labels, 1)
    runtime = time.time() - start_time
    logger.info(f"Model re-trained in {runtime:.2f} seconds.")
    return model_retrainer, runtime

def evaluate_model(model_retrainer, texts, tokens, labels):
    f5_score = model_retrainer.evaluate(texts, tokens, labels)
    logger.info(f"Model F5-Score: {f5_score}")
    return f5_score

def update_retrain_flag(entries):
    for entry in entries:
        db_manager.update_entry(DocumentEntry, {"id": entry.id}, {"for_retrain": False})
    logger.info("Reset the re-training flag for all entries.")

if __name__ == "__main__":
    app.run(port=8001, debug=True)
