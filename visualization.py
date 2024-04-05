import seaborn as sns
import matplotlib.pyplot as plt

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