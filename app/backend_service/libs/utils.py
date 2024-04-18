import psycopg2
import os

class PostgresDB:
    def __init__(self):
        self.conn = None
        self.cur = None

    def connect(self):
        DB_NAME = 'pii_db'
        DB_USER = 'ai231g1'
        DB_PASSWORD = 'ai231g1'
        DB_HOST = '127.0.0.1'
        DB_PORT = 5432

        self.conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER,
            password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
        )
        self.cur = self.conn.cursor()

    def close(self):
        self.cur.close()
        self.conn.close()

    def save_essay(self, essay):
        self.cur.execute("INSERT INTO docs.document_table (fulltext) VALUES (%s)", (essay,))
        self.conn.commit()