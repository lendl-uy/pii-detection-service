import pytest
import os
from dotenv import load_dotenv

from app.services.ml_service.constants import DEBERTA_NER, sample_text, sample_tokens
from app.services.ml_service.predictor import Predictor
from app.infra.object_store_manager import ObjectStoreManager
from app.infra.database_manager import DatabaseManager, DocumentEntry, ModelEntry

# For local testing only
# Load environment variables from .env file
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

@pytest.fixture(scope="module")
def model():
    db_manager = DatabaseManager(DB_HOST, DB_USER, DB_PASS, DB_NAME)
    s3_manager = ObjectStoreManager(S3_BUCKET_NAME)

    predictor = Predictor(DEBERTA_NER)
    predictor.get_model(s3_manager)

    yield db_manager, predictor

    # predictor.delete_model(DEBERTA_NER)
    # db_manager.clear_table(ModelEntry)
    # db_manager.clear_table(DocumentEntry)

def test_predict_sample_document_from_test_set(model):
    db_manager, predictor = model

    # Insert sample data into the database
    sample_text = """
    The Role of Technology in Enhancing Educational Outcomes
The integration of technology in education has transformed traditional teaching methodologies, enabling a more interactive, accessible, and customized learning experience. As a student at the forefront of this digital revolution, I, Michael Roberts, have personally witnessed and studied the impacts of this transformation.

My journey into the digital education world began when I enrolled at the prestigious Elite Academy, located at 5678 Education Blvd, Tech City. Here, technology isn't just an aid but the backbone of our learning process. For instance, my student ID, A9876543, grants me access to a plethora of online resources through the school's portal.

Communication technologies have particularly revolutionized how we interact with our educators and peers. During a project, I was required to coordinate with team members spread across different locations. By sharing our (555) 987-6543 contact numbers, we stayed connected and collaborated efficiently regardless of our physical distances. Additionally, setting up a project website at www.techlearnersproject.com allowed us to document our work and share our findings with a broader audience.

However, the digital age comes with its own set of challenges, especially concerning privacy and security. As USERNAME TechMike98 on educational forums and platforms, I often share insights and seek advice on complex topics. While these interactions are enriching, they also expose me to potential data breaches, necessitating cautious behavior in digital spaces.

Our identities in the digital world, such as EMAILs like michael.roberts@students.eliteacademy.edu, are not just identifiers but keys to our educational resources, personal communications, and sometimes, our digital personas. The need for robust cybersecurity measures is paramount to protect these elements of our digital lives.

Moreover, technology in education is not just about facilitating learning but also about preparing students for a future where digital literacy is as fundamental as reading and writing. Through tools like simulation software, educational games, and virtual reality, complex concepts in science, history, and mathematics are brought to life, offering an immersive learning experience that enhances comprehension and retention.

Another significant advantage of technology in education is its role in democratizing learning. Students from remote areas or with limited mobility, like Jane Thompson who lives at Remote Village, Mountain Range, can access the same quality of education as those in bustling urban centers. Online platforms and e-learning tools ensure that anyone with an internet connection can learn from the best educators without geographical barriers.

In conclusion, technology in education is a double-edged sword that, when wielded wisely, offers immense benefits. It not only enhances the learning experience through interactivity and accessibility but also prepares students for a future dominated by digital interactions. As we continue to navigate this evolving landscape, it is crucial to balance technological advancements with ethical considerations and privacy protections to fully harness the potential of digital education.
    """
    entry = DocumentEntry(full_text=sample_text)
    db_manager.add_entry(entry)

    # Retrieve the first document from the database and predict
    document = db_manager.query_entries(DocumentEntry, limit=1)[0]
    text = document.full_text if document else None

    assert text is not None, "No document retrieved."

    # Make predictions
    print(f"Predicting!")
    predictor.predict_deberta(text, DEBERTA_NER)
    print(f"Done predicting!")
    predictor.clean_up_predictions()
    predictor.save_predictions_to_database(db_manager)
    db_manager.update_entry(DocumentEntry, {"full_text": sample_text}, {"tokens": predictor.tokens})
    print(f"Cleaning up predictions")

    # Check if predictions are saved and match
    assert isinstance(predictor.predictions, list), "Predictions should be a list."

    # Reload the entry to ensure predictions are stored
    entry = db_manager.query_entries(DocumentEntry, {"full_text": text}, limit=1)[0]

    # print fulltext, tokens, labels, and predictions
    # print(f"Full Text: {entry.full_text}")
    print(f"Tokens: {entry.tokens}")
    print(f"Labels: {entry.labels}")
    print(f"Predictions: {predictor.predictions}")

    assert entry.labels == predictor.predictions, "Inserted labels do not match."