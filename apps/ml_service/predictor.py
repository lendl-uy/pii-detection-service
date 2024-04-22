import os
import zipfile
import boto3
from botocore.exceptions import NoCredentialsError

from predictor_constants import *

def download_file_from_s3(bucket, object_name, file_name):
    s3_client = boto3.client("s3")
    try:
        s3_client.download_file(bucket, object_name, file_name)
        print("File downloaded successfully")
    except NoCredentialsError:
        print("Credentials not available")

def extract_zip(zip_path, extract_to=None):
    # If no target directory provided, extract in the current directory
    if extract_to is None:
        extract_to = os.path.dirname(zip_path)
    
    # Open the zip file
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # Extract all the contents into the directory
        zip_ref.extractall(extract_to)
        print(f"All files have been extracted to: {extract_to}")

def main():

    model_name = BLANK_NER

    # Pull the PII predictor model from AWS S3 and remove unnecessary files
    if not os.path.exists(f"{MODELS_DIRECTORY}/{model_name}"):
        print("Model not found! Downloading from AWS S3")
        download_file_from_s3(S3_BUCKET_NAME, f"{MODELS_DIRECTORY}/{model_name}", model_name)

        print("Preparing the downloaded model")
        extract_zip(model_name, os.getcwd())
        os.remove(model_name)
    

if __name__ == "__main__":
    main()