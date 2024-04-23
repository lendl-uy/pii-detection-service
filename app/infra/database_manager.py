import psycopg2
from constants import DB_HOST, DB_USER, DB_PASS, DB_NAME

class DatabaseManager:

    def __init__(self, db_host=DB_HOST, db_user=DB_USER, db_pass=DB_PASS, db_name=DB_NAME):
        self.database_connection = self.connect_to_database(db_host, db_user, db_pass, db_name)

    def connect_to_database(self, db_host=DB_HOST, db_user=DB_USER, db_pass=DB_PASS, db_name=DB_NAME):
        return psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_pass,
            host=db_host
        )

    def insert_into_database(self, full_text, tokens, labels=None, validated_labels=None, for_retrain=0):
        cursor = self.database_connection.cursor()

        # Prepare the data as arrays
        full_text_array = [full_text]
        tokens_array = tokens
        labels_array = labels if labels is not None else [None]
        validated_labels_array = validated_labels if validated_labels is not None else [None]

        # Insert data into the table
        insert_query = """
        INSERT INTO document_table (full_text, tokens, labels, validated_labels, for_retrain)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (full_text_array, tokens_array, labels_array, validated_labels_array, for_retrain))
        
        self.database_connection.commit()
        cursor.close()

    def clear_database(self):
        cursor = self.database_connection.cursor()
        delete_query = "DELETE FROM document_table"
        cursor.execute(delete_query)
        
        self.database_connection.commit()
        cursor.close()