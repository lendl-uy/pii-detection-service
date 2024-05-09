import psycopg2
import os
import json
from dotenv import load_dotenv

class PostgresDB:
    def __init__(self):
        self.conn = None
        self.cur = None
        load_dotenv(dotenv_path='../.env') 

    def connect(self):
        DB_NAME = os.getenv("DB_NAME")
        DB_USER = os.getenv("DB_USER")
        DB_PASSWORD = os.getenv("DB_PASSWORD")
        DB_HOST = os.getenv("DB_HOST")
        DB_PORT = os.getenv("DB_PORT")

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

    def get_document(self,document_id):
        print("document_id",document_id)
        self.cur.execute("SELECT doc_id, tokens, labels FROM document_table WHERE doc_id = %s", (document_id,))
        document = self.cur.fetchone()
        if document:
            return {"doc_id" :document_id,"tokens": document[1], "labels":document[2]  }
        else:
            return None

    def get_documents(self, limit, offset):
        print("limit:", limit, "offset:", offset)
        self.cur.execute("SELECT doc_id, tokens, labels FROM document_table LIMIT %s OFFSET %s", (limit, offset))
        documents = self.cur.fetchall()
        if documents:
            result = []
            for doc in documents:
                result.append({"doc_id": doc[0], "tokens": doc[1], "labels": doc[2]})
            return result
        else:
            return None
