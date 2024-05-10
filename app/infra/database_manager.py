from sqlalchemy import create_engine, Column, Integer, String, Boolean, ARRAY
from sqlalchemy.orm import declarative_base, sessionmaker
from app.infra.constants import TABLE_NAME

# Updated import path for declarative_base
Base = declarative_base()

class DocumentEntry(Base):
    __tablename__ = f"{TABLE_NAME}"
    doc_id = Column(Integer, primary_key=True)
    full_text = Column(String)
    tokens = Column(ARRAY(String))
    labels = Column(ARRAY(String))
    validated_labels = Column(ARRAY(String))
    for_retrain = Column(Boolean)

class DatabaseManager:
    def __init__(self, db_host, db_user, db_pass, db_name):
        db_url = f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}/{db_name}"
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)

    def add_entry(self, entry):
        with self.Session() as session:
            session.add(entry)
            session.commit()

    def update_entry(self, entry_id, update_dict):
        with self.Session() as session:
            entry = session.query(DocumentEntry).filter(DocumentEntry.doc_id == entry_id).one_or_none()
            if entry is not None:
                for key, value in update_dict.items():
                    setattr(entry, key, value)
                session.commit()
            else:
                raise ValueError("Entry not found")

    def query_entries(self, filter_dict):
        with self.Session() as session:
            query = session.query(DocumentEntry)
            for key, value in filter_dict.items():
                query = query.filter(getattr(DocumentEntry, key) == value)
            return query.all()

    def clear_table(self):
        with self.Session() as session:
            session.query(DocumentEntry).delete()
            session.commit()