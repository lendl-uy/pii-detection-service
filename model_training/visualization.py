import seaborn as sns
import matplotlib.pyplot as plt
from collections import Counter

from training_constants import *
from read_dataset import unzip_file, read_pii_json

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
    plt.xticks(rotation=45, fontsize=10)

    # Add gridlines for y-axis
    plt.grid(axis="y", linestyle="--", alpha=0.7)

    # Add value labels above each bar
    for i, freq in enumerate(frequencies):
        plt.text(i, freq + 0.5, str(freq), ha="center", va="bottom")

    plt.tight_layout()  # Adjust layout to make room for the rotated x-axis labels
    plt.yscale("log")
    plt.show()

def main():
    # Since train.json is too large, it was zipped
    # To read the file, unzip then pass to the json parser   
    unzip_file(ZIPPED_TRAIN_SET_PATH, "../datasets/")
        
    _ , texts_train, tokens_train, _ , labels_train = read_pii_json(TRAIN_SET_PATH, is_train=True)
    _ , texts_test, tokens_test, _ = read_pii_json(TEST_SET_PATH)
    
    flat_labels = [label for sublist in labels_train for label in sublist]
    unique_labels = set(flat_labels)
    
    # Count the label frequencies
    label_counts = Counter(flat_labels)

    # Prepare data for plotting
    labels, frequencies = zip(*label_counts.items())
    
    # Don't include "O", not PIIs
    # pii_labels = labels[1:]
    # pii_frequencies = frequencies[1:]

    visualize_labels(labels, frequencies)

if __name__ == "__main__":
    main()