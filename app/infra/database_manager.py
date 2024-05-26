from sqlalchemy import create_engine, Column, Integer, String, Boolean, ARRAY, DateTime, Float, desc
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import func

# Updated import path for declarative_base
Base = declarative_base()

class DocumentEntry(Base):
    __tablename__ = "document_table"
    doc_id = Column(Integer, primary_key=True)
    full_text = Column(String)
    tokens = Column(ARRAY(String))
    labels = Column(ARRAY(String))
    validated_labels = Column(ARRAY(String))
    for_retrain = Column(Boolean)
    created_at = Column(DateTime, default=func.now())  # Automatically sets to current timestamp on creation
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())  # Updates on any modification

class ModelEntry(Base):
    __tablename__ = "model"
    doc_id = Column(Integer, primary_key=True)
    model_name = Column(String)
    runtime = Column(Float)
    predicted_at = Column(DateTime, default=func.now()) # Automatically sets to current timestamp on creation

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
                return entry.doc_id  # doc_id will be populated after commit if the insert is successful
            except Exception as e:
                session.rollback()
                print(f"Failed to add entry: {e}")
                return None

    def update_entry(self, table, filter_dict, update_dict):
        with self.Session() as session:
            entries = session.query(table)
            for key, value in filter_dict.items():
                entries = entries.filter(getattr(table, key) == value)
            if entries.count() == 0:
                raise ValueError("No entries found matching the filter criteria.")

            updated_count = 0
            for entry in entries:
                for key, value in update_dict.items():
                    setattr(entry, key, value)
                updated_count += 1

            session.commit()
            return updated_count

    def query_entries(self, table, filter_dict=None, limit=None, order_by=None, descending=False):
        with self.Session() as session:
            query = session.query(table)

            # Apply filters if any
            if filter_dict:
                for key, value in filter_dict.items():
                    query = query.filter(getattr(table, key) == value)

            # Apply ordering if specified
            if order_by:
                if descending:
                    query = query.order_by(desc(getattr(table, order_by)))
                else:
                    query = query.order_by(getattr(table, order_by))

            # Apply limit if specified
            if limit is not None:
                query = query.limit(limit)

            return query.all()

    def clear_table(self, table):
        with self.Session() as session:
            session.query(table).delete()
            session.commit()