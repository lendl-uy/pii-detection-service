import os
import psycopg2
import logging
import requests
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv

from app.services.backend_service.libs.utils import PostgresDB
from preprocessor import Preprocessor
from app.infra.database_manager import DatabaseManager, DocumentEntry

# For local testing only
# Load environment variables from .env file
load_dotenv()

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")

template_dir = os.path.abspath("../../ui/templates")
static_dir = os.path.abspath("../../ui/static")

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

# Set up logging to be info as default
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dbm = DatabaseManager(DB_HOST, DB_USER, DB_PASS, DB_NAME)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/save-essay", methods=["POST"])
def save_essay():
    # Get the essay data from the request
    data = request.json
    essay = data.get("essay")
    logger.info(f"Essay = {essay}")

    if essay:
        try:
            # Preprocess the essay inputted by the user
            logger.info("Pre-processing the input essay")
            preprocessor = Preprocessor()
            tokens = preprocessor.tokenize(essay)

            # Create and insert a new data entry to the database
            logger.info("Ingesting the essay and tokens to the database")
            entry = DocumentEntry(full_text=essay, tokens=tokens)
            doc_id = dbm.add_entry(entry)

            # Asynchronously call predict endpoint
            response = requests.post("http://127.0.0.1:5001/predict", json={"doc_id": doc_id})
            return jsonify({"message": "Essay saved and prediction requested successfully"}), 200
        except psycopg2.Error as e:
            return {"message": "Error saving essay to database: {}".format(e)}, 500
    else:
        return {"message": "No essay data provided"}, 400

@app.route("/ml-response-handler", methods=["POST"])
def handle_ml_service_response():
    # Attempt to parse the JSON data from the request
    try:
        data = request.get_json()
        doc_id = data.get("document_id")
        runtime = data.get("runtime")

        if not doc_id:
            # Missing document ID or predictions in the incoming data
            logger.error("Missing document ID in the request")
            return jsonify({"status": "FAILED", "message": "Missing document ID"}), 400

        # Log the received data
        logger.info(f"Received response for doc_id = {doc_id}")
        logger.info(f"Prediction runtime: {runtime}")

        # Here, you would typically update the database entry for the document with new data
        # Assuming you have a function update_document_entry that handles database updates
        return jsonify({"status": "SUCCESS", "message": "Document updated with predictions successfully"}), 200

    except Exception as e:
        logger.error(f"Error processing Predictor response: {str(e)}")
        return jsonify({"status": "FAILED", "message": "Error processing the Predictor response"}), 500

# Get all documents or create a new document
@app.route("/documents", methods=["GET", "POST"])
def handle_documents():
    if request.method == "GET":
        entries = dbm.query_entries(limit=10)
        documents = [{'doc_id': doc.doc_id, 'full_text': doc.full_text} for doc in entries]  # Assuming each entry has a 'name'
        logger.info(f"Documents: {documents}")
        return jsonify(documents)
    elif request.method == "POST":
        data = request.json
        if not data or 'name' not in data:
            return jsonify({'error': 'Missing required data'}), 400
        try:
            new_document = DocumentEntry(name=data['name'])
            dbm.add_entry(new_document)
            return jsonify({'id': new_document.doc_id, 'name': new_document.name}), 201
        except Exception as e:
            logger.error(f"Failed to create document: {e}")
            return jsonify({'error': 'Failed to create document'}), 500

        # or update document with user validated token

# add security feature only allowing ML_service to call this endpoint
@app.route("/labels/<int:document_id>", methods=["POST"])
def save_labels(document_id):
    data = request.json
    labels = data.get("labels")

    entry = DocumentEntry(labels=labels)
    dbm.add_entry(entry)

    return jsonify({"message": "Labels saved"}), 200


# Get individual document by ID
@app.route("/documents/<int:document_id>", methods=["GET", "PATCH"])
def get_document(document_id):
    if request.method == "PATCH":
        # Get the new label from the request
        print("patch request received")
        data = request.json
        print(data)
        validated_labels = data.get('labels')
        postgres_client = PostgresDB()

        postgres_client.connect()
        postgres_client.validate(document_id, validated_labels)

        return jsonify({"message": "Document validated"}), 200

    # default to get
    entry = dbm.query_entries({"doc_id": document_id}, limit=1)
    document = entry[0].full_text

    if document:
        return jsonify(document)
    else:
        return jsonify({"error": "Document not found"}), 404


if __name__ == '__main__':
    app.run(debug=True, port=5000)