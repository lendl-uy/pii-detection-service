import psycopg2

import os
import re

def tokenize(full_text):
    tokens = re.findall(r'\n\n+|\\u[0-9a-fA-F]{4}|[^\w\s]|[\w]+', full_text)

    return tokens

class PostgresDB:
    def __init__(self):
        self.conn = None
        self.cur = None

    def connect(self):
        DB_NAME = os.getenv('DB_NAME')
        DB_USER = os.getenv('DB_USER')
        DB_PASSWORD = os.getenv('DB_PASSWORD')
        DB_HOST = os.getenv('DB_HOST')
        DB_PORT = os.getenv('DB_PORT')

        self.conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER,
            password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
        )
        self.cur = self.conn.cursor()

    def close(self):
        self.cur.close()
        self.conn.close()

    def save_essay(self, essay, tokens):
        tokens_array = "{" + ",".join([f'"{token}"' for token in tokens]) + "}"

        insert_query = """
            INSERT INTO docs.document_table (fulltext, tokens)
            VALUES (%s, %s)
        """

        self.cur.execute(insert_query, (essay, tokens_array))
        self.conn.commit()