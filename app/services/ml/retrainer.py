import os
import random
import pandas as pd
from tqdm import tqdm
from collections import Counter, defaultdict

import spacy
from spacy.tokens import DocBin
from spacy.training import Example
from spacy.util import minibatch, compounding
from sklearn.model_selection import train_test_split


# Download training set from S3 if not available locally
if not os.path.exists(f"{DATASETS_DIRECTORY}/{INITIAL_TRAIN_SET}"):
    print("Training set not found! Downloading from AWS S3")
    download_file_from_s3(S3_BUCKET_NAME, f"{DATASETS_DIRECTORY}/{INITIAL_TRAIN_SET}", f"{DATASETS_DIRECTORY}/{INITIAL_TRAIN_SET}")

# Parse the training dataset for relevant fields
document_numbers, texts, tokens, trailing_whitespaces, labels = read_pii_json(f"{DATASETS_DIRECTORY}/{INITIAL_TRAIN_SET}", is_train=True)

# Zip the data together
zipped_data = list(zip(document_numbers, texts, tokens, trailing_whitespaces, labels))

# Perform the train-test split
train_data, test_data = train_test_split(zipped_data, test_size=0.30, random_state=0)

# Unzip the training and testing data
document_numbers_train, texts_train, tokens_train, trailing_whitespaces_train, labels_train = zip(*train_data)
document_numbers_test, texts_test, tokens_test, trailing_whitespaces_test, labels_test = zip(*test_data)