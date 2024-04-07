import json
from pymongo import MongoClient

# Simulate receiving JSON data from a web service
json_data = '''
{
  "sample_pii_data": [
    {
      "document": "100", 
      "full_text": "This is a sample essay", 
      "tokens": ["This", "is", "a", "sample", "essay"], 
      "trailing_whitespace": [false, false, false, false, false], 
      "labels": null
    }
  ]
}
'''

# Convert JSON string to a Python dictionary
data = json.loads(json_data)

# Connect to the local MongoDB database
client = MongoClient("mongodb://localhost:27017")

# Select the database and collection
db = client["ai231"]  # Use a database called 'ai231'
collection = db["pii_data_staging"]   # Use a collection called 'pii_data_staging'

# Insert the data into the collection
result = collection.insert_many(data["sample_pii_data"])

# Print the IDs of the inserted documents
print("IDs of the inserted documents:")
print(result.inserted_ids)

# Close the connection to MongoDB
client.close()