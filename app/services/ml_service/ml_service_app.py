import requests
import logging
import time
import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from app.infra.database_manager import DatabaseManager, DocumentEntry, ModelEntry
from app.infra.object_store_manager import ObjectStoreManager
from app.services.ml_service.predictor import Predictor
from app.services.ml_service.evaluator import Evaluator
from app.services.ml_service.constants import DEBERTA_NER, F5_SCORE_THRESHOLD

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
    predictor.predict_deberta(full_text, DEBERTA_NER) # Use DeBERTa
    predictor.clean_up_predictions()
    logger.info(f"Predictions = {predictor.predictions}")
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
        response = requests.post(f"http://{BACKEND_SERVICE_HOST}:5002/retrieve-predictions", json=predictor_response, headers=headers)
        if response.status_code == 200:
            return {"status": "SUCCESS", "document_id": updated_entry.doc_id, "runtime": f"{runtime:.2f} s"}, 200
        else:
            logger.error("Failed to send data to backend service.")
            return {"status": "FAILED", "message": "Error sending data to backend service."}, 500
    else:
        logger.info("Document not found in the database after update.")
        return {"status": "FAILED", "message": "Document not updated correctly."}, 400

@app.route("/evaluate-performance/<int:doc_id>", methods=["POST"])
def evaluate_model_performance(doc_id):
    evaluator = Evaluator(F5_SCORE_THRESHOLD)
    try:
        doc = db_manager.query_entries(DocumentEntry, {"doc_id" : doc_id}, limit=1)[0]
    except:
        return {"status": "FAILED", "message": "Document was not fetched properly."}, 400
    Y_true = doc.labels
    Y_pred = doc.validated_labels
    is_model_drifting = evaluator.check_for_model_drift(Y_true, Y_pred)

    if is_model_drifting:
        return ({
            "status": "FOR_RETRAINING",
            "f5-score": evaluator.f5_score,
            "message": "PII detection model is due for re-training."}
        , 200)
    else:
        return ({
            "status": "PERFORMANT",
            "f5-score": evaluator.f5_score,
            "message": "PII detection model is still performant."}
        , 200)

if __name__ == "__main__":
    # Listen on all interfaces and use port 5002
    app.run(host='0.0.0.0', port=5001, debug=True)