import requests
import logging
import time
import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv

from app.infra.database_manager import DatabaseManager, DocumentEntry
from app.infra.object_store_manager import ObjectStoreManager
from app.services.ml_service.predictor import Predictor
from app.services.ml_service.model_retrainer import ModelRetrainer
from app.services.ml_service.constants import PRETRAINED_EN_NER, ROW_COUNT_THRESHOLD_FOR_RETRAINING

# For local testing only
# Load environment variables from .env file
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

# Instantiate Flask application
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route("/predict", methods=["POST"])
def predict():
    data = request.json
    doc_id = data.get("doc_id")

    if not doc_id:
        return jsonify({"status": "FAILED", "message": "No document ID provided."}), 400

    # Instantiate connections to the database and the object store
    db_manager = DatabaseManager(DB_HOST, DB_USER, DB_PASS, DB_NAME)
    s3_manager = ObjectStoreManager(S3_BUCKET_NAME)

    # Retrieve the document to be predicted with ID specified by the preprocessor endpoint
    logger.info("Retrieving the document")
    entry = db_manager.query_entries({"doc_id": doc_id}, limit=1)
    if not entry:
        return jsonify({"status": "FAILED", "message": "Document not found."}), 404
    full_text = entry[0].full_text

    # Instantiate the predictor
    logger.info("Pulling the latest model")
    predictor = Predictor(PRETRAINED_EN_NER)
    predictor.get_model(PRETRAINED_EN_NER, s3_manager)

    if not full_text:
        logger.info("No document found for prediction.")
        return {"status": "FAILED", "message": "Document not found."}, 400

    # Perform predictions on the input full text
    logger.info("Predicting PIIs from the given full text")
    start_time = time.time()
    predictor.predict(full_text, PRETRAINED_EN_NER)
    logger.info("Done predicting PIIs")
    runtime = time.time() - start_time

    # Update the database with predictions
    if entry:
        db_manager.update_entry({"doc_id": entry[0].doc_id}, {"labels": predictor.predictions})
        updated_entry = db_manager.query_entries({"doc_id": entry[0].doc_id}, 1)[0]

        # Construct the data to send to the backend
        predictor_response = {
            "document_id": updated_entry.doc_id,
            "runtime": f"{runtime:.2f} s"
        }

        # Send predictions to the backend service
        headers = {"Content-Type": "application/json"}
        response = requests.post("http://127.0.0.1:5000/ml-response-handler", json=predictor_response, headers=headers)
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
    db_manager = DatabaseManager(DB_HOST, DB_USER, DB_PASS, DB_NAME)
    s3_manager = ObjectStoreManager(S3_BUCKET_NAME)

    try:
        # Retrieve data flagged for re-training
        entries = db_manager.query_entries({"for_retrain": True}, limit=ROW_COUNT_THRESHOLD_FOR_RETRAINING)
        if len(entries) < 3:  # Ensure there is enough data to retrain
            logger.warning("Insufficient data for re-training.")
            return {"status": "Failed", "message": "Insufficient dataset size for re-training"}, 200

        # Extract data components
        texts = [entry.full_text for entry in entries]
        tokens = [entry.tokens for entry in entries]
        labels = [entry.labels for entry in entries]

        # Initialize the model retrainer
        model_retrainer = ModelRetrainer(PRETRAINED_EN_NER)
        model_retrainer.get_model(s3_manager)

        # Split the dataset
        split_data = model_retrainer.split_dataset(texts, tokens, labels)
        texts_train, tokens_train, labels_train, texts_test, tokens_test, labels_test = split_data

        # Retrain the model
        start_time = time.time()
        model_retrainer.retrain(texts_train, tokens_train, labels_train, 1)
        runtime = time.time() - start_time
        logger.info(f"Model re-trained in {runtime:.2f} seconds.")

        # Evaluate the model
        f5_score = model_retrainer.evaluate(texts_test, tokens_test, labels_test)
        logger.info(f"Model F5-Score: {f5_score}")

        # Reset the re-training flag
        db_manager.update_entry({"for_retrain": True}, {"for_retrain": False})

        return {"status": "Success", "runtime": f"{runtime:.2f} s", "evaluation": f5_score}, 200

    except Exception as e:
        logger.error(f"Error during re-training: {str(e)}")
        return {"status": "Failed", "message": str(e)}, 500

if __name__ == "__main__":
    app.run(debug=True, port=5001)