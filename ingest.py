import json
from pymongo import MongoClient

from constants import *

# Simulate receiving JSON data from a web service
json_data = '''
{
  "sample_pii_data": [
    {
      "document": null, 
      "full_text": "This is a sample essay", 
      "tokens": null, 
      "trailing_whitespace": null, 
      "labels": null
    }
  ]
}
'''

# {
#   "sample_pii_data": [
#     {
#       "document": "100", 
#       "full_text": "This is a sample essay", 
#       "tokens": ["This", "is", "a", "sample", "essay"], 
#       "trailing_whitespace": [false, false, false, false, false], 
#       "labels": null
#     }
#   ]
# }

def ingest(json_data):

    # Convert JSON string to a Python dictionary
    data = json.loads(json_data)

    # Connect to the local MongoDB database
    # client = MongoClient(MONGODB_CONNECTION_STRING)

    # Select the database and collection
    # db = client[DATABASE_NAME]  # Use a database called 'ai231'
    # collection = db[COLLECTION_NAME_STAGING]   # Use a collection called 'pii_data_staging'

    # Insert the data into the collection
    # result = collection.insert_many(data["sample_pii_data"])

    # Print the IDs of the inserted documents
    # print("IDs of the inserted documents:")
    # print(result.inserted_ids)

    # Close the connection to MongoDB
    # client.close()

def main():
    ingest(json_data)

if __name__ == "__main__":
    main()