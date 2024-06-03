import pytest
from app.services.ml_service.evaluator import Evaluator
from app.services.ml_service.constants import F5_SCORE_THRESHOLD

import random

# Possible labels
labels = [
    'O', 'B-EMAIL', 'B-ID_NUM', 'B-NAME_STUDENT', 'B-PHONE_NUM',
    'B-STREET_ADDRESS', 'B-URL_PERSONAL', 'B-USERNAME', 'I-ID_NUM',
    'I-NAME_STUDENT', 'I-PHONE_NUM', 'I-STREET_ADDRESS', 'I-URL_PERSONAL'
]

@pytest.fixture(scope="function")
def evaluator():
    evaluator = Evaluator(F5_SCORE_THRESHOLD)
    yield evaluator

def generate_labels(labels, n_samples=200, error_rate=0.2):
    # Generate random true labels
    Y_true = [random.choice(labels) for _ in range(n_samples)]

    # Generate predicted labels with some noise
    Y_pred = []
    n_indices = [i for i in range(n_samples)]
    random.shuffle(n_indices)

    for true_label in Y_true:
        Y_pred.append(true_label)

    for i in range(int(n_samples * error_rate)):
        index = n_indices[i]
        labels_copy = labels.copy()
        original_label = Y_pred[index]
        labels_copy.remove(original_label)
        Y_pred[index] = random.choice(labels_copy)

    return Y_true, Y_pred

def test_check_below_f5_score_threshold(evaluator):
    # Generate random true labels and pred labels that have errors
    Y_true, Y_pred = generate_labels(labels, error_rate=1-F5_SCORE_THRESHOLD+0.1)
    is_model_drifting = evaluator.check_for_model_drift(Y_true, Y_pred)
    assert is_model_drifting == True

def test_check_above_f5_score_threshold(evaluator):
    # Generate random true labels and pred labels that have errors
    Y_true, Y_pred = generate_labels(labels, error_rate=1-F5_SCORE_THRESHOLD-0.1)
    is_model_drifting = evaluator.check_for_model_drift(Y_true, Y_pred)
    assert is_model_drifting == False

def test_check_equal_to_f5_score_threshold(evaluator):
    # Generate random true labels and pred labels that have errors
    Y_true, Y_pred = generate_labels(labels, error_rate=1-F5_SCORE_THRESHOLD)
    is_model_drifting = evaluator.check_for_model_drift(Y_true, Y_pred)
    assert is_model_drifting == False