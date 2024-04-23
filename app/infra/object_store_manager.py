import boto3
from botocore.exceptions import NoCredentialsError

class ObjectStoreManager:

    def __init__(self, bucket):
        self.bucket = bucket

    def download_from_s3(self, object_name, file_name):
        # Initialize an S3 client
        s3_client = boto3.client("s3")
        try:
            # Download the file/object from the specified bucket name to the destination path
            s3_client.download_file(self.bucket, object_name, file_name)
            print("File downloaded successfully")
        except NoCredentialsError:
            print("Credentials not available")

    def upload_to_s3(self, object_name, file_name):
        # Initialize an S3 client
        s3_client = boto3.client("s3")