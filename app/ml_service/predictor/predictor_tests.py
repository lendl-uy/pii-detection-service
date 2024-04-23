import json
from predictor_constants import BLANK_NER
from predictor import load_model, delete_model, predict

def predict_sample_document_from_test_set():

    model_name = BLANK_NER

    load_model(model_name)

    # Obtain the document in JSON file format
    sample_documents = open("test.json")
    # Convert JSON string to a Python dictionary
    documents = json.load(sample_documents)
    # Retrieve only one document for testing
    document = documents[0]["full_text"]

    predictions = predict(document, model_name)
    print(f"predictions = {predictions}")

    delete_model(model_name)

def main():
    predict_sample_document_from_test_set()
    
if __name__ == "__main__":
    main()