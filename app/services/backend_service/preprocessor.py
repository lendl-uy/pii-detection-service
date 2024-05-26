import json
import re
import codecs

class Preprocessor:

    def __init__(self):
        self.full_text = None
        self.tokens = None

    def parse_json(self, response_name, json_data):
        # Convert JSON string to a Python dictionary
        data = json.load(json_data)

        # Obtain the essay
        self.full_text = data[response_name][0]["full_text"]

        return self.full_text

    def decode_escapes(self, input_text):
        # Decode all escape sequences using the unicode_escape codec
        return codecs.decode(input_text, 'unicode_escape')

    def tokenize(self, full_text):
        # Use regular expression to find sequences of word characters, punctuation, special characters, or whitespace.
        # This pattern attempts to keep sequences of non-space special characters intact while splitting other tokens correctly.
        self.tokens = re.findall(r'\n\n+|\\u[0-9a-fA-F]{4}|[^\w\s]|[\w]+', self.decode_escapes(full_text))
        return self.tokens