import os
import zipfile
import spacy
import shutil
import torch
import json
from transformers import AutoTokenizer, AutoModelForTokenClassification
from pathlib import Path

from app.services.ml_service.constants import MODELS_DIRECTORY, INFERENCE_MAX_LENGTH
from app.infra.database_manager import DocumentEntry

class Predictor:
    def __init__(self, model_name):
        self.model_name = model_name
        self.document = None
        self.predictions = None
        self.tokens = None
        self.tokens_as_vectors = None

    def extract_zip(self, zip_path, extract_to=None):
        if extract_to is None:
            extract_to = os.path.dirname(zip_path)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
            print(f"All files have been extracted to: {extract_to}")

    def get_model(self, object_store):
        model_path = f"{self.model_name}.zip"
        if not os.path.exists(self.model_name):
            print("Model not found! Downloading from AWS S3")
            object_store.download(f"{MODELS_DIRECTORY}/{self.model_name}.zip", model_path)
            print("Preparing the downloaded model")
            self.extract_zip(model_path, os.getcwd())
            os.remove(model_path)

    def delete_model(self, model_path):
        if os.path.exists(model_path):
            try:
                shutil.rmtree(model_path)
                print(f"The model {model_path} has been successfully deleted.")
            except Exception as e:
                print(f"Failed to delete the model: {e}")
        else:
            print(f"The specified model {model_path} does not exist.")

    def predict(self, document, model_name):
        nlp = spacy.load(model_name)
        self.document = document
        doc = nlp(document)
        self.predictions = [(token.ent_type_ if token.ent_type_.startswith(('B-', 'I-')) else "O") for token in doc]

        tokens = []

        for token, label in zip(doc, self.predictions):
            tokens.append(str(token))
        self.tokens = tokens

    def tokenize_deberta(self, document, model_name):
        self.document = document
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.tokens_as_vectors = self.tokenizer(document, return_tensors="pt", truncation=True, max_length=INFERENCE_MAX_LENGTH)
        self.tokens = self.tokenizer.convert_ids_to_tokens(self.tokens_as_vectors.input_ids[0])

    def predict_deberta(self, document, model_name):
        # Tokenize the document into a format suitable for DeBERTa
        self.tokenize_deberta(document, model_name)

        # Initialize the model
        model = AutoModelForTokenClassification.from_pretrained(model_name)

        # Load id2label mapping
        config = json.load(open(Path(model_name) / "config.json"))
        id2label = config["id2label"]

        # Predict
        model.eval()
        with torch.no_grad():
            outputs = model(**self.tokens_as_vectors)
        logits = outputs.logits

        # Obtain predictions for non-special, non-padded tokens
        predictions = logits.argmax(dim=-1).squeeze(0)  # Remove the batch dimension
        active_tokens = self.tokens_as_vectors['attention_mask'].squeeze(0) == 1  # Identify non-padded tokens

        # Filter out predictions for special and padded tokens
        filtered_predictions = predictions[active_tokens]

        # Convert predictions to labels
        self.predictions = [id2label[str(pred.item())] for pred in filtered_predictions]

        return self.predictions

    def save_predictions_to_database(self, db_manager):
        entry = db_manager.query_entries(DocumentEntry, {"full_text": self.document}, limit=1)[0]
        if entry:
            db_manager.update_entry(DocumentEntry, {"full_text": self.document}, {"labels": self.predictions})
        else:
            print("Document not found in the database.")