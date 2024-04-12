import json
import mysql.connector
from db_constants import *

def connect_to_database(db_host=DB_HOST, db_user=DB_USER, db_pass=DB_PASS, db_name=DB_NAME):
    return mysql.connector.connect(
        host=db_host,
        user=db_user,
        passwd=db_pass,
        database=db_name
    )

def insert_into_database(full_text, tokens, connection, labels=None, validated_labels=None, for_retrain=0):
    cursor = connection.cursor()

    # Convert the full text and tokens to JSON
    full_text_json = json.dumps({"text": full_text})
    tokens_json = json.dumps({"tokens": tokens})

    # Initialize JSON objects for labels if they are not None, else use JSON null
    labels_json = json.dumps(labels) if labels is not None else json.dumps(None)
    validated_labels_json = json.dumps(validated_labels) if validated_labels is not None else json.dumps(None)

    # Insert full text and tokens into the table as JSON
    insert_query = """
    INSERT INTO document_table (full_text, token, labels, validated_labels, for_retrain)
    VALUES (%s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, (full_text_json, tokens_json, labels_json, validated_labels_json, for_retrain))
    
    connection.commit()
    cursor.close()

def clear_database(connection):
    cursor = connection.cursor()

    # Insert full text and tokens into the table as JSON
    delete_query = """
    DELETE FROM document_table
    """
    cursor.execute(delete_query)
    
    connection.commit()
    cursor.close()