import json
import zipfile

def unzip_file(source_path, destination_path="."):
    try:
        with zipfile.ZipFile(source_path, "r") as zip_ref:
            # Extract all the contents into the directory specified
            zip_ref.extractall(destination_path)
    except Exception as e:
        # Corrected exception handling syntax
        raise RuntimeError(f"{e} occurred!") from e
    

def read_pii_json(file_path, is_train=False):
    # Initialize an empty list to store the data
    data = []

    # Open the JSON file and load its contents into the list
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"FileNotFoundError: The file {file_path} was not found.")
    except json.JSONDecodeError:
        raise json.JSONDecodeError("JSONDecodeError: Error decoding JSON from the file.")
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred: {e}")
        
    document_numbers = [data[i]["document"] for i in range(len(data))]
    texts = [data[i]["full_text"] for i in range(len(data))]
    tokens = [data[i]["tokens"] for i in range(len(data))]
    trailing_whitespaces = [data[i]["trailing_whitespace"] for i in range(len(data))]
    
    # print(document_numbers)
    # print(texts)
    # print(tokens)
    # print(trailing_whitespaces)
        
    if is_train:
        labels = [data[i]["labels"] for i in range(len(data))]
        return document_numbers, texts, tokens, trailing_whitespaces, labels
    else:
        return document_numbers, texts, tokens, trailing_whitespaces