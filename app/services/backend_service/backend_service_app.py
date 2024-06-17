import os
import logging
import requests

import psycopg2
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from dotenv import load_dotenv
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user


from app.services.backend_service.preprocessor import Preprocessor
from app.services.backend_service.validation_preprocessor import ValidationPreprocessor
from app.infra.database_manager import DatabaseManager, DocumentEntry, User

# Load environment variables from .env file
load_dotenv()

# Database configuration
DB_CONFIG = {
    "db_host": os.getenv("DB_HOST"),
    "db_user": os.getenv("DB_USER"),
    "db_pass": os.getenv("DB_PASS"),
    "db_name": os.getenv("DB_NAME")
}

# ML Service Host
ML_SERVICE_HOST = os.getenv("ML_SERVICE_HOST")

# Flask app setup
template_dir = os.path.abspath("app/ui/templates")
static_dir = os.path.abspath("app/ui/static")
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)


# Logger setup
app.secret_key = os.getenv("APP_SECRET_KEY")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database manager initialization
db_manager = DatabaseManager(**DB_CONFIG)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    session = db_manager.Session()
    user = session.query(User).get(int(user_id))
    session.close()
    return user

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        session = db_manager.Session()
        
        user = User(username=username)
        user.set_password(password)
        session.add(user)
        session.commit()
        session.close()
        flash('User registered successfully.')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        

        session = db_manager.Session()
        user = session.query(User).filter_by(username=username).first()
        
        session.close()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully.')
            return redirect(url_for('save_essay_view'))
        else:
            flash('Invalid username or password.')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('index'))


@app.route("/")
def index():
    return render_template("home.html")

@app.route("/save-essay-view")
@login_required
def save_essay_view():
    #get user
    user = current_user

    flash('Some notification about poorly performing model.')
    return render_template("save_essay_view.html",username=user.username)

@app.route("/predictions-view")
@login_required
def predictions_view():
    #get user
    user = current_user
    return render_template("predictions_view.html",username=user.username)

# Endpoint to render the validation page
@app.route("/validate/<int:doc_id>")
def validate(doc_id):
    return render_template("validate.html")

@app.route("/save-essay", methods=["POST"])
def save_essay():
    data = request.get_json()
    essay = data.get("essay")

    if not essay:
        return jsonify({"message": "No essay data provided"}), 400

    try:    
        cleaned_essay = Preprocessor().decode_escapes(essay)
        document_entry = DocumentEntry(full_text=cleaned_essay)
        doc_id = db_manager.add_entry(document_entry)

        response = requests.post(f"http://{ML_SERVICE_HOST}:8081/predict", json={"doc_id": doc_id})
        return jsonify({"message": "Essay saved and prediction requested successfully"}), 200
    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        return jsonify({"message": f"Database error: {e}"}), 500
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({"message": f"Unexpected error: {e}"}), 500

@app.route("/retrieve-predictions", methods=["GET", "POST"])
def retrieve_predictions():
    if request.method == "POST":
        return handle_post_predictions()
    else:
        return handle_get_predictions()

def handle_post_predictions():
    data = request.get_json()
    doc_id = data.get("document_id")
    runtime = data.get("runtime")

    preprocessor = Preprocessor()

    if not doc_id:
        logger.error("Missing document ID in POST request")
        return jsonify({"status": "FAILED", "message": "Missing document ID"}), 400

    try:
        entry = fetch_document_entry(doc_id)
        if not entry:
            logger.error("Document not found")
            return jsonify({"status": "FAILED", "message": "Document not found"}), 404
        tokens, predictions = entry.tokens, entry.labels
        cleaned_tokens = preprocessor.clean_tokens_deberta(tokens)
        cleaned_predictions = predictions[1:-1]
        logger.info(f"Received POST response for doc_id = {doc_id}, runtime = {runtime}")
        logger.info(f"Tokens: {cleaned_tokens}")
        logger.info(f"Predictions: {cleaned_predictions}")

        if cleaned_predictions:
            return jsonify({"status": "SUCCESS", "tokens": cleaned_tokens, "predictions": cleaned_predictions}), 200
        else:
            return jsonify({"status": "FAILED", "message": "No predictions found"}), 404
    except Exception as e:
        logger.error(f"Error processing POST predictor response: {str(e)}")
        return jsonify({"status": "FAILED", "message": f"Error: {str(e)}"}), 500

def handle_get_predictions():
    doc_id = request.args.get('doc_id')
    preprocessor = Preprocessor()
    if not doc_id:
        logger.error("Missing document ID in GET query")
        return jsonify({"status": "FAILED", "message": "Missing document ID"}), 400

    try:
        entry = fetch_document_entry(doc_id)
        if not entry:
            logger.error("Document not found")
            return jsonify({"status": "FAILED", "message": "Document not found"}), 404

        full_text = entry.full_text
        logger.info(f"full_text = {full_text}")
        logger.info(f"Retrieved GET predictions for doc_id = {doc_id}")
        tokens, predictions = entry.tokens, entry.labels
        cleaned_tokens = preprocessor.clean_tokens_deberta(tokens)
        cleaned_predictions = predictions[1:-1]
        logger.info(f"Retrieved GET predictions for doc_id = {doc_id}")
        logger.info(f"Tokens: {cleaned_tokens}")
        logger.info(f"Predictions: {cleaned_predictions}")

        return jsonify({"status": "SUCCESS", "tokens": cleaned_tokens, "predictions": cleaned_predictions}), 200
    except Exception as e:
        logger.error(f"Error retrieving GET predictions: {str(e)}")
        return jsonify({"status": "FAILED", "message": f"Error: {str(e)}"}), 500

def fetch_document_entry(doc_id):
    """Fetch a single document entry from the database."""
    entries = db_manager.query_entries(DocumentEntry, {"doc_id": doc_id}, limit=1)
    return entries[0] if entries else None

# Endpoint to get all documents
@app.route('/documents')
def get_documents():
    try:
        documents = fetch_documents_with_labels()
        return jsonify([format_document(doc) for doc in documents]), 200
    except Exception as e:
        logger.error(f"Failed to retrieve documents: {e}")
        return jsonify({"error": "Failed to retrieve documents"}), 500

def fetch_documents_with_labels():
    """Fetches documents from the database with labels, discarding those without labels."""
    documents = db_manager.query_entries(DocumentEntry, {}, limit=10, order_by="updated_at", descending=True)
    return [doc for doc in documents if doc.labels is not None]

def format_document(doc):
    """Formats the document's data for JSON response."""
    truncated_text = truncate_text(doc.full_text)
    labels = preprocess_labels(doc)
    cleaned_tokens = doc.tokens[1:-1]
    cleaned_labels = labels[1:-1]
    logger.info(f"cleaned_tokens = {cleaned_tokens}")
    logger.info(f"cleaned_labels = {cleaned_labels}")
    merged_cleaned_tokens, merged_cleaned_labels = merge_tokens_and_labels(cleaned_tokens, cleaned_labels)
    return {
        'doc_id': doc.doc_id,
        'truncated_text': truncated_text,
        'full_text': doc.full_text,
        'tokens': merged_cleaned_tokens,
        'labels': merged_cleaned_labels
    }

def truncate_text(text):
    """Truncates text to 50 characters with an ellipsis if longer than 27 characters."""
    return text[:50] + "..." if len(text) > 50 else text

def preprocess_labels(doc):
    """Applies label preprocessing to either validated or unvalidated labels."""
    validation_preprocessor = ValidationPreprocessor()
    labels = doc.validated_labels if doc.validated_labels else doc.labels
    return validation_preprocessor.remove_prefixes(labels)

# Endpoint to get a specific document
@app.route('/document/<int:doc_id>')
def get_document(doc_id):
    try:
        document = fetch_document_by_id(doc_id)
        if not document:
            return jsonify({"message": "Document not found"}), 404

        formatted_document = format_document_detail(document)
        return jsonify(formatted_document), 200
    except Exception as e:
        logger.error(f"Failed to retrieve document {doc_id}: {e}")
        return jsonify({"error": "Failed to retrieve document"}), 500

def fetch_document_by_id(doc_id):
    """Fetch a single document entry from the database."""
    entries = db_manager.query_entries(DocumentEntry, {"doc_id": doc_id}, limit=1)
    return entries[0] if entries else None


def merge_tokens_and_labels(tokens, labels):
    merged_tokens = []
    merged_labels = []

    current_token = ""
    current_label = ""
    token_sequence_start = True

    padded_tokens = tokens + ["▁"]
    padded_labels = labels + ["O"]

    for i in range(len(tokens)):
        token = padded_tokens[i]
        label = padded_labels[i]
        next_token = padded_tokens[i + 1]
        next_label = padded_labels[i + 1]
        if label == next_label:
            if not next_token.startswith("▁"):
                current_label = label
                if token_sequence_start:
                    current_token += token + next_token
                    token_sequence_start = False
                else:
                    current_token += next_token
            else:
                if current_token:
                    # print(f"Appending here 1 | token = {current_token}")
                    merged_tokens.append(current_token)
                    merged_labels.append(current_label)
                    current_token = ""
                    token_sequence_start = True
                else:
                    # print(f"Appending here 5 | token = {token}")
                    merged_tokens.append(token)
                    merged_labels.append(label)
        else:
            if current_token:
                # print(f"Appending here 2 | token = {current_token}")
                merged_tokens.append(current_token)
                merged_labels.append(current_label)
                current_token = ""
                token_sequence_start = True
            else:
                # print(f"Appending here 6 | token = {token}")
                merged_tokens.append(token)
                merged_labels.append(label)
    return merged_tokens, merged_labels

def format_document_detail(document):
    """Formats detailed document data for JSON response."""
    validation_preprocessor = ValidationPreprocessor()
    labels = get_processed_labels(document, validation_preprocessor)
    cleaned_tokens = document.tokens[1:-1]
    cleaned_labels = labels[1:-1]
    logger.info(f"cleaned_tokens = {cleaned_tokens}")
    merged_cleaned_tokens, merged_cleaned_labels = merge_tokens_and_labels(cleaned_tokens, cleaned_labels)
    return {
        'doc_id': document.doc_id,
        'full_text': document.full_text,
        'tokens': merged_cleaned_tokens,
        'labels': merged_cleaned_labels
    }

def get_processed_labels(document, validation_preprocessor):
    """Processes document labels through the validation preprocessor."""
    labels_to_process = document.validated_labels if document.validated_labels else document.labels
    return validation_preprocessor.remove_prefixes(labels_to_process) if labels_to_process else []

# Endpoint to update a label
@app.route("/update-labels", methods=["POST"])
def update_labels():
    try:
        updates = request.get_json()
        if not updates:
            return jsonify({"message": "No updates provided"}), 400

        logger.info(f"Received updates: {updates}")
        return process_label_updates(updates)
    except Exception as e:
        logger.error(f"Failed to process updates: {e}")
        return jsonify({"error": "Failed to process updates"}), 500

def process_label_updates(updates):
    """Processes label updates and applies changes to the database."""
    response_messages = []
    for update in updates:
        doc_id = update.get('docId')
        document = fetch_document(doc_id)
        tokens = update.get('tokens')
        if not document:
            response_messages.append({"message": f"Document with ID {doc_id} not found", "status": "error"})
            continue

        token_index = update.get('tokenIndex')
        new_label = update.get('newLabel')

        logger.info(f"UPDATE: {new_label} at {token_index}")
        updated_labels = update_labels_in_document(document, tokens, token_index, new_label)

        if updated_labels:
            db_manager.update_entry(DocumentEntry, {"doc_id": doc_id}, {"validated_labels": updated_labels})
            response_messages.append({"message": f"Labels updated for document ID {doc_id}", "status": "success"})
        else:
            response_messages.append(
                {"message": f"Failed to update labels for document ID {doc_id}", "status": "error"})

    return jsonify(response_messages), 200

def rebuild_fragmented_tokens(tokens, merged_tokens):
    token_dictionary = {}
    temp_string = ""
    j = 0
    k = 1
    for i in range(len(tokens)):
        token = tokens[i]
        temp_string += token
        merged_token = merged_tokens[j]
        if temp_string == merged_token:
            # token_index_tuple = (merged_tokens[j], j)
            if len(tokens[i - k:i]) > 1:
                token_dictionary[j] = tokens[i - k + 1:i + 1]
            else:
                token_dictionary[j] = tokens[i:i + 1]
            j += 1
            temp_string = ""
            k = 1
        else:
            k += 1
    return token_dictionary

def fetch_document(doc_id):
    """Fetches a single document entry from the database."""
    entries = db_manager.query_entries(DocumentEntry, {"doc_id": doc_id}, limit=1)
    return entries[0] if entries else None

def update_labels_in_document(document, tokens, token_index, new_label):
    """Updates labels in a document based on the token index and new label provided."""
    validation_preprocessor = ValidationPreprocessor()
    labels = document.labels if document.validated_labels is None else document.validated_labels

    # Build dictionary of tokens mapping DeBERTa's tokens and custom tokens
    deberta_custom_tokens_dict = rebuild_fragmented_tokens(document.tokens[1:-1], tokens)
    token_count = len(deberta_custom_tokens_dict[token_index])
    first_deberta_token = deberta_custom_tokens_dict[token_index][0]
    starting_index = document.tokens.index(first_deberta_token)
    for i in range(starting_index, starting_index + token_count):
        # logger.info(f"token_index = {i}")
        previous_label = labels[i - 1] if i > 0 else "O"
        # logger.info(f"previous_label = {previous_label}")
        prefix = determine_prefix(previous_label, new_label, validation_preprocessor)
        labels[i] = prefix + new_label
        next_label = (labels[i + 1]) if i < len(labels) - 1 else "O"
        # logger.info(f"next_label = {next_label}")
        cleaned_next_label = validation_preprocessor.remove_prefixes([next_label])[0]
        # logger.info(f"cleaned_next_label = {cleaned_next_label}")
        if cleaned_next_label != "O":
            if new_label != cleaned_next_label:
                labels[i + 1] = "B-" + cleaned_next_label
            else:
                labels[i + 1] = "I-" + cleaned_next_label
    return labels

def determine_prefix(previous_label, new_label, preprocessor):
    """Determines the prefix for a label based on the previous label and the new label."""
    previous_label_no_prefix = preprocessor.remove_prefixes([previous_label])[0]
    new_label_no_prefix = preprocessor.remove_prefixes([new_label])[0]
    if new_label == "O":
        return ""
    elif previous_label_no_prefix == new_label_no_prefix and previous_label != "O":
        return "I-"
    else:
        return "B-"


if __name__ == '__main__':
    # Use port 5002. and listen on all interfaces.
    app.run(host='0.0.0.0', port=5002, debug=True)