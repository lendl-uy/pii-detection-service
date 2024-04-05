from collections import Counter

from constants import *
from read_dataset import *
from visualization import *

def main():
       
    # Since train.json is too large, it was zipped
    # To read the file, unzip then pass to the json parser   
    unzip_file(ZIPPED_TRAIN_SET_PATH, "datasets/")
        
    document_numbers_train, texts_train, tokens_train, trailing_whitespaces_train, labels_train = read_pii_json(TRAIN_SET_PATH, is_train=True)
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