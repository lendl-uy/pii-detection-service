import os
from app.infra.database_manager import DatabaseManager

db = DatabaseManager()

# def ingest_json_data_no_labels():
#     # Ingest sample JSON file
#     if not os.path.exists(PATH_TO_SAMPLE_ESSAY):
#         print("Sample JSON file not found! Downloading from AWS S3")
#         download_file_from_s3("ai231-pii-detection", "datasets/sample_input.json", PATH_TO_SAMPLE_ESSAY)
#     ingest(PATH_TO_SAMPLE_ESSAY)

#     # Clear database
#     db_connection = connect_to_database(DB_HOST, DB_USER, DB_PASS, DB_NAME)
#     clear_database(db_connection)
#     db_connection.close()

# def main():
#     ingest_json_data_no_labels()

# if __name__ == "__main__":
#     main()