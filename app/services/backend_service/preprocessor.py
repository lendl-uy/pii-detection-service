import json
import re
import codecs

class Preprocessor:

    def __init__(self):
        self.full_text = None
        self.full_text_cleaned = None
        self.tokens = None

    def parse_json(self, response_name, json_data):
        # Convert JSON string to a Python dictionary
        data = json.load(json_data)

        # Obtain the essay
        self.full_text = data[response_name][0]["full_text"]

        return self.full_text

    def decode_escapes(self, input_text):
        # Decode all escape sequences using the unicode_escape codec
        self.full_text_cleaned = codecs.decode(input_text, "unicode_escape")
        return self.full_text_cleaned

    def tokenize(self, full_text):
        # Use regular expression to find sequences of word characters, punctuation, special characters, or whitespace.
        # This pattern attempts to keep sequences of non-space special characters intact while splitting other tokens correctly.
        self.tokens = re.findall(r'\n\n+|\\u[0-9a-fA-F]{4}|[^\w\s]|[\w]+', self.decode_escapes(full_text))
        return self.tokens

    def reconstruct_text(self, tokens, labels):
        # Initialize an empty string for the reconstructed text
        reconstructed_text = ""
        # Loop through each token and corresponding label
        for token, label in zip(tokens, labels):
            # Skip special tokens
            if token in ["[CLS]", "[SEP]"]:
                continue
            # Remove the first underscore and any subsequent underscores (subword pieces)
            if token.startswith("▁"):
                # Add a space before starting a new word (if not the start of the string)
                if reconstructed_text:
                    reconstructed_text += " "
                # Add the cleaned token (without the underscore)
                reconstructed_text += token[1:]
            else:
                # Directly append subword pieces to the last word (no space)
                reconstructed_text += token

        return reconstructed_text

    def clean_tokens_deberta(self, tokens):
        # Remove [CLS] and [SEP]
        removed_stream_identifiers = tokens[1:-1]
        # Remove first underscores
        removed_underscores = [token[1:] if (token.startswith("▁") and len(token) > 1) else token for token in
                               removed_stream_identifiers]
        return removed_underscores