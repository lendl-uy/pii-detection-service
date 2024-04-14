import json
import boto3
from botocore.exceptions import NoCredentialsError
    
def read_pii_json(file_path, is_train=False):
    # Initialize an empty list to store the data
    data = []

    # Open the JSON file and load its contents into the list
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"FileNotFoundError: The file {file_path} was not found.")
    except json.JSONDecodeError:
        raise json.JSONDecodeError("JSONDecodeError: Error decoding JSON from the file.")
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred: {e}")
     
    # Extract the values of the keys and store in dedicated lists   
    document_numbers = [data[i]["document"] for i in range(len(data))]
    texts = [data[i]["full_text"] for i in range(len(data))]
    tokens = [data[i]["tokens"] for i in range(len(data))]
    trailing_whitespaces = [data[i]["trailing_whitespace"] for i in range(len(data))]
      
    # Training set has an extra key "label"  
    if is_train:
        labels = [data[i]["labels"] for i in range(len(data))]
        return document_numbers, texts, tokens, trailing_whitespaces, labels
    else:
        return document_numbers, texts, tokens, trailing_whitespaces

def upload_file_to_s3(file_name, bucket, object_name=None):
    if object_name is None:
        object_name = file_name
    s3_client = boto3.client("s3")
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
        print("File uploaded successfully")
    except FileNotFoundError:
        print("The file was not found")
    except NoCredentialsError:
        print("Credentials not available")

def download_file_from_s3(bucket, object_name, file_name):
    s3_client = boto3.client("s3")
    try:
        s3_client.download_file(bucket, object_name, file_name)
        print("File downloaded successfully")
    except NoCredentialsError:
        print("Credentials not available")