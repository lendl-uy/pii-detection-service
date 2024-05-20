import os
import zipfile
import spacy
import shutil

from app.services.ml_service.constants import MODELS_DIRECTORY
from app.infra.database_manager import DocumentEntry

class Predictor:
    def __init__(self, model_name):
        self.model_name = model_name
        self.document = None
        self.predictions = None

    def extract_zip(self, zip_path, extract_to=None):
        if extract_to is None:
            extract_to = os.path.dirname(zip_path)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
            print(f"All files have been extracted to: {extract_to}")

    def get_model(self, model_name, object_store):
        model_path = f"{model_name}.zip"
        if not os.path.exists(model_name):
            print("Model not found! Downloading from AWS S3")
            object_store.download(f"{MODELS_DIRECTORY}/{model_name}.zip", model_path)
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

    def save_predictions_to_database(self, db_manager):
        entry = db_manager.query_entries(DocumentEntry, {"full_text": self.document}, limit=1)[0]
        if entry:
            db_manager.update_entry(DocumentEntry, {"full_text": self.document}, {"labels": self.predictions})
        else:
            print("Document not found in the database.")