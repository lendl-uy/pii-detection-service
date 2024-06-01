import pytest
import os
import boto3
from moto import mock_aws
from dotenv import load_dotenv
from app.infra.object_store_manager import ObjectStoreManager

# For local testing only
# Load environment variables from .env file
load_dotenv()

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "test"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "test"
    os.environ["AWS_SECURITY_TOKEN"] = "test"
    os.environ["AWS_SESSION_TOKEN"] = "test"

@pytest.fixture
def s3_client(aws_credentials):
    with mock_aws():
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket=S3_BUCKET_NAME)
        yield s3

@pytest.fixture
def object_store_manager(s3_client):
    """Create an ObjectStoreManager instance with a mocked S3 client."""
    return ObjectStoreManager(S3_BUCKET_NAME)


def test_upload(object_store_manager):
    """Test the upload functionality."""
    # Create a test file
    with open("test.txt", "w") as f:
        f.write('Hello, world!')

    object_store_manager.upload("test.txt", "test.txt")

    # Verify the file was uploaded
    body = object_store_manager.s3_client.get_object(Bucket=S3_BUCKET_NAME, Key="test.txt")["Body"]
    assert body.read().decode() == "Hello, world!"

def test_download(object_store_manager):
    """Test the download functionality."""
    object_store_manager.s3_client.put_object(Bucket=S3_BUCKET_NAME, Key="download.txt", Body="Download me!")

    object_store_manager.download("datasets/download.txt", "datasets/downloaded.txt")

    # Verify the file was downloaded
    with open("downloaded.txt", "r") as f:
        content = f.read()
    assert content == "Download me!"

def test_delete(object_store_manager):
    """Test the delete functionality."""
    object_store_manager.s3_client.put_object(Bucket=S3_BUCKET_NAME, Key="delete_me.txt", Body="Delete me!")

    object_store_manager.delete("delete_me.txt")

    # Verify the file was deleted
    with pytest.raises(object_store_manager.s3_client.exceptions.NoSuchKey):
        object_store_manager.s3_client.get_object(Bucket=S3_BUCKET_NAME, Key="delete_me.txt")


def test_delete_directory(object_store_manager):
    """Test the delete directory functionality."""
    object_store_manager.s3_client.put_object(Bucket=S3_BUCKET_NAME, Key="folder/file1.txt", Body="File 1")
    object_store_manager.s3_client.put_object(Bucket=S3_BUCKET_NAME, Key="folder/file2.txt", Body="File 2")

    object_store_manager.delete_directory('folder/')

    # Verify the directory was deleted
    response = object_store_manager.s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix="folder/")
    assert "Contents" not in response