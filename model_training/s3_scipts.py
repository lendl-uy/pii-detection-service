import boto3
from botocore.exceptions import NoCredentialsError

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