import os
import seaborn as sns
import matplotlib.pyplot as plt
from collections import Counter

from training_constants import *
from read_dataset import download_file_from_s3, read_pii_json

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
    
    if not os.path.exists(f"{DATASETS_DIRECTORY}/{INITIAL_TRAIN_SET}"):
        print("Training set not found! Downloading from AWS S3")
        download_file_from_s3(S3_BUCKET_NAME, f"{DATASETS_DIRECTORY}/{INITIAL_TRAIN_SET}", f"{DATASETS_DIRECTORY}/{INITIAL_TRAIN_SET}")
    if not os.path.exists(f"{DATASETS_DIRECTORY}/{INITIAL_TEST_SET}"):
        print("Test set not found! Downloading from AWS S3")
        download_file_from_s3(S3_BUCKET_NAME, f"{DATASETS_DIRECTORY}/{INITIAL_TEST_SET}", f"{DATASETS_DIRECTORY}/{INITIAL_TEST_SET}")
        
    _ , texts_train, tokens_train, _ , labels_train = read_pii_json(f"{DATASETS_DIRECTORY}/{INITIAL_TRAIN_SET}", is_train=True)
    _ , texts_test, tokens_test, _ = read_pii_json(f"{DATASETS_DIRECTORY}/{INITIAL_TEST_SET}")
    
    flat_labels = [label for sublist in labels_train for label in sublist]
    unique_labels = set(flat_labels)
    
    # Count the label frequencies
    label_counts = Counter(flat_labels)

    # Prepare data for plotting
    labels, frequencies = zip(*label_counts.items())

    visualize_labels(labels, frequencies)

if __name__ == "__main__":
    main()