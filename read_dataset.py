import json
import zipfile
import seaborn as sns
import matplotlib.pyplot as plt
from collections import Counter

from constants import * 

def read_pii_json(file_path, is_train=False):
    
    # Initialize an empty list to store the data
    data = []

    # Open the JSON file and load its contents into the list
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"The file {file_path} was not found.")
    except json.JSONDecodeError:
        print("Error decoding JSON from the file.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        
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
    
def visualize_labels(labels, frequencies):
    
    # Plot the bar chart
    sns.set(style="whitegrid")

    plt.figure(figsize=(10, 8))

    # Define a color palette
    colors = sns.color_palette("husl", len(labels))  # 'husl' is a nice colorful palette

    # Plot bars with colors
    plt.bar(labels, frequencies, color=colors)

    plt.xlabel("Labels", fontsize=14)  # Adjust font size as needed
    plt.ylabel("Frequency", fontsize=14)
    plt.title("Frequency of Each Label", fontsize=16)

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45, fontsize=12)

    # Add gridlines for y-axis
    plt.grid(axis="y", linestyle="--", alpha=0.7)

    # Add value labels above each bar
    for i, freq in enumerate(frequencies):
        plt.text(i, freq + 0.5, str(freq), ha="center", va="bottom")

    plt.tight_layout()  # Adjust layout to make room for the rotated x-axis labels
    plt.show()
        

def main():
       
    # Since train.json is too large, it was zipped
    # To read the file, unzip then pass to the json parser 
    with zipfile.ZipFile(TRAIN_SET_PATH, "r") as zip_ref:
        # Extract all the contents into the directory specified
        zip_ref.extractall("datasets")
        
    document_numbers_train, texts_train, tokens_train, trailing_whitespaces_train, labels_train = read_pii_json(TRAIN_SET_PATH[:-4], is_train=True)
    document_numbers_test, texts_test, tokens_test, trailing_whitespaces_test = read_pii_json(TEST_SET_PATH)
        
    flat_labels = [label for sublist in labels_train for label in sublist]
    unique_labels = set(flat_labels)
    
    # Count the label frequencies
    label_counts = Counter(flat_labels)

    # Prepare data for plotting
    labels, frequencies = zip(*label_counts.items())
    
    # Don't include "O", not PIIs
    pii_labels = labels[1:]
    pii_frequencies = frequencies[1:]
    
    visualize_labels(pii_labels, pii_frequencies)
    
    
if __name__ == "__main__":
    main()