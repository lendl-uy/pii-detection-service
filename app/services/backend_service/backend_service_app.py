import os
import psycopg2
import logging
import requests
from flask import Flask, request, jsonify, render_template, redirect, url_for
from dotenv import load_dotenv

from preprocessor import Preprocessor
from validation_preprocessor import ValidationPreprocessor
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
    return render_template("home.html")

@app.route("/save-essay-view")
def save_essay_view():
    return render_template("save_essay_view.html")

@app.route("/predictions-view")
def predictions_view():
    return render_template("predictions_view.html")

@app.route("/save-essay", methods=["POST"])
def save_essay():
    # Get the essay data from the request
    data = request.json
    essay = data["essay"]
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

            response = requests.post("http://127.0.0.1:5002/predict", json={"doc_id": doc_id})
            return jsonify({"message": "Essay saved and prediction requested successfully"}), 200
        except psycopg2.Error as e:
            return {"message": "Error saving essay to database: {}".format(e)}, 500
    else:
        return {"message": "No essay data provided"}, 400

@app.route("/retrieve-predictions", methods=["GET", "POST"])
def retrieve_predictions():

    if request.method == "POST":
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

            entry = dbm.query_entries(DocumentEntry, {"doc_id": doc_id}, limit=1)
            tokens = entry[0].tokens
            predictions = entry[0].labels
            logger.info(f"tokens: {tokens}")
            logger.info(f"predictions: {predictions}")

            if predictions:
                # return redirect(url_for("predictions_view"))
                return jsonify({"status": "SUCCESS", "tokens": tokens, "predictions": predictions}), 200
            else:
                return jsonify({"status": "FAILED", "message": "No predictions found"}), 404
        except Exception as e:
            logger.error(f"Error processing Predictor response: {str(e)}")
            return jsonify({"status": "FAILED", "message": "Error processing the Predictor response"}), 500

    elif request.method == "GET":
        # Logic to handle GET request to fetch and display predictions
        doc_id = request.args.get('doc_id')
        if not doc_id:
            logger.error("Missing document ID in query")
            return jsonify({"status": "FAILED", "message": "Missing document ID"}), 400

        try:
            entry = dbm.query_entries(DocumentEntry, {"doc_id": doc_id}, limit=1)
            if entry:
                tokens = entry[0].tokens
                predictions = entry[0].labels
                logger.info(f"tokens: {tokens}")
                logger.info(f"predictions: {predictions}")

                return jsonify({"status": "SUCCESS", "tokens": tokens, "predictions": predictions}), 200
            else:
                logger.error("Document not found")
                return jsonify({"status": "FAILED", "message": "Document not found"}), 404
        except Exception as e:
            logger.error(f"Error retrieving predictions: {str(e)}")
            return jsonify({"status": "FAILED", "message": "Error retrieving predictions"}), 500


# Endpoint to get all documents
@app.route('/documents')
def get_documents():
    documents = dbm.query_entries(DocumentEntry, {}, limit=10, order_by="updated_at", descending=True)
    validation_preprocessor = ValidationPreprocessor()
    for doc in documents:
        if doc.labels is None:
            logger.warning(f"Document {doc.doc_id} has no labels!")
            documents.remove(doc)
    docs = [
        {'doc_id': doc.doc_id,
         'truncated_text': doc.full_text[:30]
                           + "..." if len(doc.full_text) > 27 else doc.full_text[:30],
         'full_text': doc.full_text,
         'tokens': doc.tokens,
         'labels': validation_preprocessor.remove_prefixes(doc.labels) if doc.validated_labels is None else doc.validated_labels}
        for doc in documents
    ]
    return jsonify(docs)

# Endpoint to get a specific document
@app.route('/document/<int:doc_id>')
def get_document(doc_id):
    document = dbm.query_entries(DocumentEntry, {"doc_id": doc_id}, limit=1)[0]
    doc = {
        'doc_id': document.doc_id,
        'full_text': document.full_text,
        'tokens': document.tokens,
        'labels': document.labels if document.validated_labels is None else document.validated_labels
    }
    return jsonify(doc)

# Endpoint to update a label
@app.route('/update-labels', methods=['POST'])
def update_labels():
    updates = request.get_json()
    response_messages = []
    logger.info(f"updates = {updates}")

    doc_id = updates[0]['docId']
    document = dbm.query_entries(DocumentEntry, {"doc_id": doc_id}, limit=1)[0]
    validated_labels = document.labels

    for update in updates:
        doc_id = update['docId']
        token_index = update['tokenIndex']
        new_label = update['newLabel']
        document = dbm.query_entries(DocumentEntry, {"doc_id": doc_id}, limit=1)[0]
        logger.info(f"token_index = {token_index}, label = {document.labels}, new_label = {new_label}")
        if document:
            previous_label = validated_labels[token_index-1]
            prefix = "B-" if previous_label == "O" else "I-"
            validated_labels[token_index] = prefix + new_label
        else:
            response_messages.append({'message': f'Document with ID {doc_id} not found', 'status': 'error'})

    dbm.update_entry(DocumentEntry, {"doc_id": doc_id}, {"validated_labels": validated_labels})

    return jsonify(response_messages), 200

# Endpoint to render the validation page
@app.route('/validate/<int:doc_id>')
def validate(doc_id):
    return render_template('validate.html')


if __name__ == '__main__':
    app.run(debug=True, port=5001)