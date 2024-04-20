from flask import Flask, request
import psycopg2

from libs.utils import PostgresDB, tokenize

import logging

app = Flask(__name__)

# Set up logging to be info as default
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/save-essay', methods=['POST'])
def save_essay():
    # Get the essay data from the request
    data = request.json
    essay = data.get('essay')

    if essay:
        # Tokenize the essay
        tokens = tokenize(essay)

        try:
            # Connect to PostgreSQL
            postgres_client = PostgresDB()
            postgres_client.connect()

            logger.info('Saving essay to database')

            postgres_client.save_essay(essay, tokens)
            postgres_client.close()

            return {'message': 'Essay saved successfully'}, 200
        except psycopg2.Error as e:
            return {'message': 'Error saving essay to database: {}'.format(e)}, 500
    else:
        return {'message': 'No essay data provided'}, 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
