from sqlalchemy import create_engine, Column, Integer, String, Boolean, ARRAY
from sqlalchemy.orm import declarative_base, sessionmaker
from app.infra.constants import TABLE_NAME
import logging

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
            try:
                session.add(entry)
                session.commit()
            except Exception as e:
                session.rollback()
                print(f"Failed to add entry: {e}")

    def update_entry(self, filter_dict, update_dict):
        with self.Session() as session:
            entries = session.query(DocumentEntry)
            for key, value in filter_dict.items():
                entries = entries.filter(getattr(DocumentEntry, key) == value)
            if entries.count() == 0:
                raise ValueError("No entries found matching the filter criteria.")

            updated_count = 0
            for entry in entries:
                for key, value in update_dict.items():
                    setattr(entry, key, value)
                updated_count += 1

            session.commit()
            return updated_count

    def query_entries(self, filter_dict=None, limit=None):
        with self.Session() as session:
            query = session.query(DocumentEntry)
            if filter_dict:
                for key, value in filter_dict.items():
                    query = query.filter(getattr(DocumentEntry, key) == value)
            if limit is not None:
                query = query.limit(limit)
            return query.all()

    def clear_table(self):
        with self.Session() as session:
            session.query(DocumentEntry).delete()
            session.commit()