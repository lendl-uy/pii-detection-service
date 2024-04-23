import json
import re
import boto3
from botocore.exceptions import NoCredentialsError
from app.infra.db_scripts import connect_to_database, insert_into_database

def parse_json(json_data):
    # Convert JSON string to a Python dictionary
    data = json.load(json_data)

    # Obtain the essay
    full_text = data["sample_pii_data"][0]["full_text"]
    
    return full_text

def tokenize(full_text):
    # Use regular expression to find sequences of word characters, punctuation, special characters, or whitespace.
    # This pattern attempts to keep sequences of non-space special characters intact while splitting other tokens correctly.
    tokens = re.findall(r'\n\n+|\\u[0-9a-fA-F]{4}|[^\w\s]|[\w]+', full_text)

    return tokens

def ingest(path):
    try:
        # Open the JSON file
        sample_essay = open(path)

        # Obtain then preprocess data
        full_text = parse_json(sample_essay)
        tokens = tokenize(full_text)

        # Connect to the database
        db_connection = connect_to_database()

        # Insert data into the database
        insert_into_database(full_text, tokens, db_connection)

        db_connection.close()

        print("Data inserted successfully.")

    except Exception as e:
        print(f"An error occurred: {str(e)}")