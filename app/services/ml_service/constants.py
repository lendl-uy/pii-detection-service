# Dataset directory and filenames
MODELS_DIRECTORY = "models"
BLANK_NER = "pii_ner_blank_spacy"
PRETRAINED_EN_NER = "pii_ner_pretrained_sm_spacy"

# Dataset directory and filenames
DATASETS_DIRECTORY = "datasets"
INITIAL_TRAIN_SET = "train.json"
INITIAL_TEST_SET = "test.json"

# Model parameters
EPOCHS = 5
DROPOUT_RATE = 0.3

# Sample data for the predictor
sample_text = "John Doe, a 35-year-old software engineer, lives at 1234 Maple Drive, Springfield, IL. He moved there in June 2015. You can reach him at his personal email, john.doe@example.com, or his mobile phone, 555-123-4567. John's previous address was 987 Elm Street, Centerville, OH."
sample_tokens = ['John', 'Doe', ',', 'a', '35', '-', 'year', '-', 'old', 'software', 'engineer', ',', 'lives', 'at', '1234', 'Maple', 'Drive', ',', 'Springfield', ',', 'IL', '.', 'He', 'moved', 'there', 'in', 'June', '2015', '.', 'You', 'can', 'reach', 'him', 'at', 'his', 'personal', 'email', ',', 'john', '.', 'doe', '@', 'example', '.', 'com', ',', 'or', 'his', 'mobile', 'phone', ',', '555', '-', '123', '-', '4567', '.', 'John', "'", 's', 'previous', 'address', 'was', '987', 'Elm', 'Street', ',', 'Centerville', ',', 'OH', '.']

# Sample data for the model re-trainer
sample_text_1 = "Alice Johnson called from 212-555-1234. Her email is alice.j@example.com."
sample_tokens_1 = ["Alice", "Johnson", "called", "from", "212-555-1234", ".", "Her", "email", "is", "alice.j@example.com", "."]
sample_labels_1 = ["B-NAME", "I-NAME", "O", "O", "B-PHONE", "O", "O", "O", "O", "B-EMAIL", "O"]

sample_text_2 = "Dr. Robert Smith will see you now. His office number at 456 Elm St is 415-555-9876."
sample_tokens_2 = ["Dr.", "Robert", "Smith", "will", "see", "you", "now", ".", "His", "office", "number", "at", "456", "Elm", "St", "is", "415-555-9876", "."]
sample_labels_2 = ["O", "B-NAME", "I-NAME", "O", "O", "O", "O", "O", "O", "O", "O", "O", "B-ADDRESS", "I-ADDRESS", "I-ADDRESS", "O", "B-PHONE", "O"]