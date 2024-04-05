import json

from constants import * 

def read_pii_json(file_path):
    
    # Initialize an empty list to store the data
    data_list = []

    # Open the JSON file and load its contents into the list
    try:
        with open(file_path, "r") as file:
            data_list = json.load(file)
    except FileNotFoundError:
        print(f"The file {file_path} was not found.")
    except json.JSONDecodeError:
        print("Error decoding JSON from the file.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        
    document_numbers = [data_list[i]["document"] for i in range(len(data_list))]
    texts = [data_list[i]["full_text"] for i in range(len(data_list))]
    tokens = [data_list[i]["tokens"] for i in range(len(data_list))]
    trailing_whitespaces = [data_list[i]["trailing_whitespace"] for i in range(len(data_list))]
    
    # print(document_numbers)
    # print(texts)
    # print(tokens)
    # print(trailing_whitespaces)
    
    return document_numbers, texts, tokens, trailing_whitespaces


def main():
    
    document_numbers_train, texts_train, tokens_train, trailing_whitespaces_train = read_pii_json(TRAIN_SET_PATH)
    document_numbers_test, texts_test, tokens_test, trailing_whitespaces_test = read_pii_json(TEST_SET_PATH)
        
    
if __name__ == "__main__":
    main()