import psycopg2
from psycopg2.extensions import AsIs
from psycopg2 import sql

class DatabaseManager:
    def __init__(self, db_host, db_user, db_pass, db_name):
        self.db_host = db_host
        self.db_user = db_user
        self.db_pass = db_pass
        self.db_name = db_name

    def connect(self):
        self.db_connection = psycopg2.connect(
            dbname=self.db_name,
            user=self.db_user,
            password=self.db_pass,
            host=self.db_host
        )
        return self.db_connection

    def disconnect(self):
        self.db_connection.close()

    def insert(self, table_name, full_text=None, tokens=None, labels=None, validated_labels=None, for_retrain=False):
        cursor = self.db_connection.cursor()

        try:
            # Prepare data as arrays, using placeholders for None inputs
            labels_array = labels if labels is not None else [None]
            validated_labels_array = validated_labels if validated_labels is not None else [None]

            table_name = psycopg2.extensions.quote_ident(table_name, cursor)

            # Prepare the insert query
            query = f"""
                    INSERT INTO {table_name} (full_text, tokens, labels, validated_labels, for_retrain)
                    VALUES (%s, %s, %s, %s, %s)
                    """

            cursor.execute(query, (full_text, tokens, labels_array, validated_labels_array, for_retrain))

            # Commit changes and close cursor
            self.db_connection.commit()

        except Exception as e:
            # Roll back any changes if an exception occurred
            self.db_connection.rollback()
            print(f"Unable to insert row to the database: {e}")
            return False

        finally:
            cursor.close()

        return True

    def update(self, table_name, column, column_value, qualifier, qualifier_value):
        cursor = self.db_connection.cursor()

        try:
            # Safely quote the table and column names using psycopg2.sql
            query = sql.SQL("UPDATE {table} SET {column} = %s WHERE {qualifier} = %s").format(
                table=sql.Identifier(table_name),
                column=sql.Identifier(column),
                qualifier=sql.Identifier(qualifier)
            )

            cursor.execute(query, (column_value, qualifier_value))

            # Commit changes and close cursor
            self.db_connection.commit()

        except Exception as e:
            # Roll back any changes if an exception occurred
            self.db_connection.rollback()
            print(f"Unable to update row in the database: {e}")
            return False

        finally:
            cursor.close()

        return True

    def query(self, query, params=None):
        cursor = self.db_connection.cursor()
        try:
            cursor.execute(query, params)
            result = cursor.fetchone()
            return result
        except psycopg2.Error as e:
            print(f"Database error: {e}")
            return None
        finally:
            cursor.close()

    def clear(self, table_name):
        cursor = self.db_connection.cursor()
        try:
            safe_table_name = psycopg2.extensions.quote_ident(table_name, cursor)
            delete_query = f"DELETE FROM {safe_table_name}"
            cursor.execute(delete_query)
            self.db_connection.commit()
        except Exception as e:
            self.db_connection.rollback()
            print(f"Error clearing table {table_name}: {e}")
        finally:
            cursor.close()