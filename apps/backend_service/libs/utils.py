"""
    Utility functions
"""
import os
import re

import psycopg2

def tokenize(full_text):
    """
        Tokenize the input full text
    """
    tokens = re.findall(r'\n\n+|\\u[0-9a-fA-F]{4}|[^\w\s]|[\w]+', full_text)

    return tokens

class PostgresDB:
    """
        PostgreSQL database client
    """
    def __init__(self):
        self.conn = None
        self.cur = None

    def connect(self):
        """
            Connect to PostgreSQL database
        """
        db_name = os.getenv('DB_NAME')
        db_user = os.getenv('DB_USER')
        db_pw = os.getenv('DB_PASSWORD')
        db_host = os.getenv('DB_HOST')
        db_port = os.getenv('DB_PORT')

        self.conn = psycopg2.connect(
            dbname=db_name, user=db_user,
            password=db_pw, host=db_host, port=db_port
        )
        self.cur = self.conn.cursor()

    def close(self):
        """
            Close the PostgreSQL database connection
        """
        self.cur.close()
        self.conn.close()

    def save_essay(self, essay, tokens):
        """
            Save the essay to the database
        """
        tokens_array = "{" + ",".join([f'"{token}"' for token in tokens]) + "}"

        insert_query = """
            INSERT INTO docs.document_table (fulltext, tokens)
            VALUES (%s, %s)
        """

        self.cur.execute(insert_query, (essay, tokens_array))
        self.conn.commit()
