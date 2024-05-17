import os
import random
import datetime
import zipfile
import shutil
import re
import spacy
from spacy.tokens import DocBin
from spacy.training import Example
from spacy.util import minibatch, compounding
from sklearn.model_selection import train_test_split
from tqdm import tqdm

from app.services.ml_service.constants import *

class ModelRetrainer:

    def __init__(self, model_name):
        self.model_name = model_name

    def split_dataset(self, texts, tokens, labels):
        # Zip the data together
        zipped_data = list(zip(texts, tokens, labels))

        # Perform the train-test split
        train_data, test_data = train_test_split(zipped_data, test_size=0.30, random_state=0)

        # Unzip the training and testing data
        texts_train, tokens_train, labels_train = zip(*train_data)
        texts_test, tokens_test, labels_test = zip(*test_data)

        return texts_train, tokens_train, labels_train, texts_test, tokens_test, labels_test

    def extract_zip(self, zip_path, extract_to=None):
        # If no target directory provided, extract in the current directory
        if extract_to is None:
            extract_to = os.path.dirname(zip_path)

        # Open the zip file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Extract all the contents into the directory
            zip_ref.extractall(extract_to)
            print(f"All files have been extracted to: {extract_to}")

    def get_model(self, object_store):
        # Pull the PII predictor model from the object store and remove unnecessary files
        if not os.path.exists(self.model_name):
            print("Model not found! Downloading from AWS S3")
            object_store.download(f"{MODELS_DIRECTORY}/{self.model_name}.zip", f"{self.model_name}.zip")

            print("Preparing the downloaded model")
            self.extract_zip(f"{self.model_name}.zip", os.getcwd())
            os.remove(f"{self.model_name}.zip")

    def prepare_documents(self, nlp, texts, tokens, labels):
        # Initialize DocBin to store the training examples
        doc_bin = DocBin()

        annotated_data = []

        # Wrap the main loop with tqdm for progress visualization
        for text, doc_tokens, doc_labels in tqdm(zip(texts, tokens, labels), total=len(texts),
                                                 desc="Processing Documents"):
            doc = nlp.make_doc(text)
            ents = []
            position = 0

            for token, label in zip(doc_tokens, doc_labels):
                if label != "O":
                    start_actual = text.find(token, position)
                    end_actual = start_actual + len(token)

                    # Catch instances when substring is not found from the text
                    if start_actual == -1:
                        raise ValueError(f"Token '{token}' not found from the text[{position}]!")
                    ents.append((start_actual, end_actual, label))

                    position = end_actual

            annotated_data.append((text, {"entities": ents}))
            # Append the example to DocBin
            example = Example.from_dict(doc, {"entities": ents})
            doc_bin.add(example.reference)
        return doc_bin, annotated_data

    def fbeta_score(self, precision, recall, beta=5):
        if precision == 0.0 or recall == 0.0:
            return 0.0
        return (1 + beta ** 2) * (precision * recall) / ((beta ** 2 * precision) + recall)

    def retrain(self, texts_train, tokens_train, labels_train, epochs=EPOCHS):
        # Load the pre-trained spaCy model
        self.model = spacy.load(self.model_name)

        # Create a new entity recognizer and add it to the pipeline if it's not already present
        if "ner" not in self.model.pipe_names:
            ner = self.model.add_pipe("ner")
        else:
            ner = self.model.get_pipe("ner")

        doc_bin_train, annotated_data = self.prepare_documents(self.model, texts_train, tokens_train, labels_train)

        # Load the serialized data from DocBin
        train_data = list(doc_bin_train.get_docs(self.model.vocab))  # This will create a list of Doc objects

        # Create Example objects required for training
        examples = []
        for doc in tqdm(train_data, desc="Processing Docs"):
            examples.append(
                Example.from_dict(doc, {"entities": [(ent.start_char, ent.end_char, ent.label_) for ent in doc.ents]}))

        # Add labels to the NER
        for example in tqdm(examples, desc="Adding Labels"):
            for ent in example.reference.ents:
                ner.add_label(ent.label_)

        # Train the NER model
        # Reference for loss computation: https://github.com/explosion/spaCy/discussions/9128
        optimizer = self.model.resume_training()
        batch_sizes = compounding(8.0, 64.0, 1.001)  # Dynamically change batch size from 8 to 64

        for i in tqdm(range(epochs), desc="Fine-tuning Pre-trained Model"):
            losses = {}
            random.shuffle(examples)  # Shuffle the training data before each iteration
            batches = minibatch(examples, size=batch_sizes)  # Create minibatches
            for batch in batches:
                self.model.update(batch, drop=DROPOUT_RATE, losses=losses)
            print(f"Losses at iteration {i}: {losses}")

    def evaluate(self, texts_test, tokens_test, labels_test):
        # Load the trained model
        nlp = self.model

        doc_bin_test, annotated_data = self.prepare_documents(nlp, texts_test, tokens_test, labels_test)

        test_data = list(doc_bin_test.get_docs(nlp.vocab))

        # Create Example objects for the test set
        test_examples = [
            Example.from_dict(doc, {"entities": [(ent.start_char, ent.end_char, ent.label_) for ent in doc.ents]}) for
            doc in test_data]

        # After training, evaluate on the test set
        scorer = nlp.evaluate(test_examples)
        precision = scorer["ents_p"]
        recall = scorer["ents_r"]
        f5_score = self.fbeta_score(precision, recall, beta=5)

        # print("Evaluation Metrics:")
        # print(f"F5-Score: {f5_score}")
        # print(f"Precision: {precision}")
        # print(f"Recall: {recall}")

        return f5_score

    def extract_model_name_regex(self, str):
        # Match any characters up to the last occurrence of a potential date pattern
        match = re.match(r"^(.*?)(-\d{4}-\d{2}-\d{2})?$", str)
        return match.group(1) if match else None

    def zip_model(self, folder_path, output_path):
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Walk through directory
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    # Create a relative path for files to keep the directory structure
                    rel_path = os.path.relpath(os.path.join(root, file), os.path.dirname(folder_path))
                    zipf.write(os.path.join(root, file), arcname=rel_path)

    def delete_model(self, model_path):
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

    def delete_model_zipped(self, model_path):
        try:
            os.remove(model_path)
            print(f"File {model_path} successfully deleted.")
        except FileNotFoundError:
            print(f"The file {model_path} does not exist.")
        except PermissionError:
            print(f"Permission denied: unable to delete {model_path}.")
        except Exception as e:
            print(f"An error occurred while deleting the file: {e}")

    def save_and_upload_model(self, object_store):
        # Get the current local date
        current_date = datetime.date.today()

        orig_model_name_no_date = self.extract_model_name_regex(self.model_name)
        new_model_name = f"{orig_model_name_no_date}-{current_date}"

        self.model.to_disk(new_model_name)

        self.zip_model(new_model_name, f"{new_model_name}.zip")
        self.delete_model(self.model_name)

        object_store.upload(f"{new_model_name}.zip", f"models/{new_model_name}.zip")

        self.delete_model(new_model_name)
        self.delete_model_zipped(f"{new_model_name}.zip")