from ingest import ingest
from db_scripts import connect_to_database, clear_database
from db_constants import *

def ingest_json_data_no_labels():
    # Ingest sample JSON file
    ingest(PATH_TO_SAMPLE_ESSAY)

    # Clear database
    db_connection = connect_to_database(DB_HOST, DB_USER, DB_PASS, DB_NAME)
    clear_database(db_connection)
    db_connection.close()

def main():
    ingest_json_data_no_labels()

if __name__ == "__main__":
    main()