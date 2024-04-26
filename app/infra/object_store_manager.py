import boto3
from botocore.exceptions import NoCredentialsError

class ObjectStoreManager:
    def __init__(self, name):
        self.name = name
        self.s3_client = boto3.client("s3")

    def download(self, object_name, file_name):
        try:
            self.s3_client.download_file(self.name, object_name, file_name)
            print("File downloaded successfully")
        except NoCredentialsError:
            print("Credentials not available")
        except Exception as e:
            print(f"An error occurred while downloading the file: {e}")

    def upload(self, file_name, object_name):
        try:
            self.s3_client.upload_file(file_name, self.name, object_name)
            print("File uploaded successfully")
        except NoCredentialsError:
            print("Credentials not available")
        except Exception as e:
            print(f"An error occurred while uploading the file: {e}")

    def delete(self, object_name):
        try:
            # Delete a single object
            self.s3_client.delete_object(Bucket=self.name, Key=object_name)
            print("File deleted successfully")
        except NoCredentialsError:
            print("Credentials not available")
        except Exception as e:
            print(f"An error occurred while deleting the file: {e}")

    def delete_directory(self, prefix):
        try:
            # List all objects with the specified prefix
            response = self.s3_client.list_objects_v2(Bucket=self.name, Prefix=prefix)
            if 'Contents' in response:
                # Delete each object in the directory
                for obj in response['Contents']:
                    self.s3_client.delete_object(Bucket=self.name, Key=obj['Key'])
                print("Directory deleted successfully")
            else:
                print("Directory is empty or does not exist")
        except NoCredentialsError:
            print("Credentials not available")
        except Exception as e:
            print(f"An error occurred while deleting the directory: {e}")
