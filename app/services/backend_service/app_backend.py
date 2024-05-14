from flask import Flask, request, jsonify,render_template
import os
import psycopg2

from libs.utils import PostgresDB
from preprocessor import Preprocessor
from app.infra.database_manager import DatabaseManager
from app.infra.constants import *

DB_NAME = DB_NAME
DB_USER = DB_USER
DB_PASSWORD = DB_PASS
DB_HOST = DB_HOST
DB_PORT = 5432


import logging

template_dir = os.path.abspath('app/ui')

app = Flask(__name__, template_folder=template_dir)

# Set up logging to be info as default
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/save-essay', methods=['POST'])
def save_essay():
    # Get the essay data from the request
    data = request.json
    essay = data.get('essay')


    if essay:
        try:
            # Connect to PostgreSQL
            #postgres_client = PostgresDB()
            #postgres_client.connect()

            logger.info('Saving essay to database')
            dbm=DatabaseManager(DB_HOST,DB_USER,DB_PASSWORD,DB_NAME)
            dbm.connect()

            #run preprocessor
            preprocessor=Preprocessor()
            tokens = preprocessor.tokenize(essay)

            #call ml_service

            preprocessor.ingest_to_database(essay,tokens,dbm)



            # Save the essay to the database
            #postgres_client.save_essay(essay)

            # Close the connection
            #postgres_client.close()

            #send fulltext to ml_service for tokenization


            return {'message': 'Essay saved successfully'}, 200
        except psycopg2.Error as e:
            return {'message': 'Error saving essay to database: {}'.format(e)}, 500
    else:
        return {'message': 'No essay data provided'}, 400


# Get all documents or create a new document
@app.route('/documents', methods=['GET', 'POST'])
def handle_documents():
    if request.method == 'GET':
        postgres_client = PostgresDB()
        postgres_client.connect()
        
        documents = postgres_client.get_documents(limit=10, offset=0)

        return jsonify(documents)
    elif request.method == 'POST':
        global next_id
        data = request.json
        new_document = {"id": next_id, "name": data["name"]}  # assuming data contains "name" field
        documents.append(new_document)
        next_id += 1
        return jsonify(new_document), 201



        #or update document with user validated token






#add security feature only allowing ML_service to call this endpoint
@app.route('/labels/<int:document_id>', methods=['POST'])
def save_labels(document_id):
    data = request.json
    labels = data.get('labels')

    postgres_client = PostgresDB()
    postgres_client.connect()

    postgres_client.save_labels(document_id, labels)

    return jsonify({"message": "Labels saved"}), 200


# Get individual document by ID
@app.route('/documents/<int:document_id>', methods=['GET','PATCH'])
def get_document(document_id):

    if request.method == 'PATCH':
        # Get the new label from the request
        print("patch request received")
        data = request.json
        print(data)
        validated_labels= data.get('labels')
        postgres_client = PostgresDB()
        
        postgres_client.connect()
        postgres_client.validate(document_id,validated_labels)

        return jsonify({"message": "Document validated"}), 200

        


    #default to get
    postgres_client = PostgresDB()
    postgres_client.connect()

    document = postgres_client.get_document(document_id)

    if document:
        return jsonify(document)

    else:
        return jsonify({"error": "Document not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)
