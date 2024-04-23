import os
import zipfile
import spacy
import shutil

from predictor_constants import *

class Predictor:

    def __init__(self, model_name):
        self.get_model(model_name)

    def extract_zip(self, zip_path, extract_to=None):
        # If no target directory provided, extract in the current directory
        if extract_to is None:
            extract_to = os.path.dirname(zip_path)
        
        # Open the zip file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Extract all the contents into the directory
            zip_ref.extractall(extract_to)
            print(f"All files have been extracted to: {extract_to}")

    def delete_model(model_path):
        # Check if the model already exists
        if os.path.exists(model_path):
            try:
                # Delete the model directory, including the contents of the directory
                shutil.rmtree(model_path)
                print(f"The model {model_path} has been successfully deleted.")
            except Exception as e:
                print(f"Failed to delete the model: {e}")
        else:
            print(f"The specified model {model_path} does not exist.")

    def get_model(self, model_name):
        # Pull the PII predictor model from AWS S3 and remove unnecessary files
        if not os.path.exists(model_name):
            print("Model not found! Downloading from AWS S3")
            self.download_file_from_s3(S3_BUCKET_NAME, f"{MODELS_DIRECTORY}/{model_name}.zip", f"{model_name}.zip")

            print("Preparing the downloaded model")
            self.extract_zip(f"{model_name}.zip", os.getcwd())
            os.remove(f"{model_name}.zip")

    def delete_model(model_path):
        # Check if the model already exists
        if os.path.exists(model_path):
            try:
                # Delete the model directory, including the contents of the directory
                shutil.rmtree(model_path)
                print(f"The model {model_path} has been successfully deleted.")
            except Exception as e:
                print(f"Failed to delete the model: {e}")
        else:
            print(f"The specified model {model_path} does not exist.")

    def predict(document, model_name):
        # Load the specified trained model
        nlp = spacy.load(model_name)

        # Predict the PII entities from the input document
        doc = nlp(document)

        # Stored predicted labels as a list
        predictions = []
        for token in doc:
            ent_type = token.ent_type_
            if ent_type.startswith(('"B-"', "I-")):
                predictions.append(ent_type)
            else:
                predictions.append("O")

        return predictions