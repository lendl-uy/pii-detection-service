import json
import re

class Preprocessor:

    def __init__(self):
        pass
    
    def parse_json(self, json_data):
        # Convert JSON string to a Python dictionary
        data = json.load(json_data)

        # Obtain the essay
        full_text = data["sample_pii_data"][0]["full_text"]
        
        return full_text

    def tokenize(self, full_text):
        # Use regular expression to find sequences of word characters, punctuation, special characters, or whitespace.
        # This pattern attempts to keep sequences of non-space special characters intact while splitting other tokens correctly.
        tokens = re.findall(r'\n\n+|\\u[0-9a-fA-F]{4}|[^\w\s]|[\w]+', full_text)

        return tokens