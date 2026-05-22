#!/usr/bin/env python3

"""
    a function called filter_datum that returns the log message obfuscated
"""
import re
from typing import List
import logging
import os
import mysql.connector
from mysql.connector import connection

PII_FIELDS = ("name", "email", "phone", "ssn", "password")


def filter_datum(fields: List[str], redaction: str,
                 message: str, separator: str) -> str:
    """
        returns the log message obfuscated

        Args:
        fields (List[str]): A list of strings representing all
        fields to obfuscate.
        redaction (str): A string representing by what the field
        will be obfuscated.
        message (str): A string representing the log line.
        separator (str): A string representing by which character
        is separating all fields in the log line.
    """
    pattern = '|'.join([f'{field}=[^ {separator}]+' for field in fields])
    return re.sub(pattern, lambda m: f'{m.group().split("=")[0]}={redaction}',
                  message)


class RedactingFormatter(logging.Formatter):
    """ Redacting Formatter class
    """

    REDACTION = "***"
    FORMAT = "[HOLBERTON] %(name)s %(levelname)s %(asctime)-15s: %(message)s"
    SEPARATOR = ";"

    def __init__(self, fields: List[str]):
        """init method"""

        super(RedactingFormatter, self).__init__(self.FORMAT)
        self.fields = fields

    def format(self, record: logging.LogRecord) -> str:
        """filters values in incoming log records using filter_datum"""

        original_message = super().format(record)
        return filter_datum(self.fields, self.REDACTION,
                            original_message, self.SEPARATOR)


def get_logger() -> logging.Logger:
    """
    Creates and returns a logger named 'user_data'.

    The logger logs up to logging.INFO level and has
    a StreamHandler with RedactingFormatter.
    """
    logger = logging.getLogger("user_data")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # Create StreamHandler with RedactingFormatter
    handler = logging.StreamHandler()
    formatter = RedactingFormatter(PII_FIELDS)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def get_db() -> connection.MySQLConnection:
    """
    Connects to a MySQL database using credentials
    from environment variables and returns the connection object.

    Environment Variables:
        PERSONAL_DATA_DB_USERNAME: Database username (default: "root").
        PERSONAL_DATA_DB_PASSWORD: Database password (default: "").
        PERSONAL_DATA_DB_HOST: Database host (default: "localhost").
        PERSONAL_DATA_DB_NAME: Database name.

    Returns:
        mysql.connector.connection.MySQLConnection:
        Database connection object.
    """

    db_username = os.getenv('PERSONAL_DATA_DB_USERNAME', 'root')
    db_password = os.getenv('PERSONAL_DATA_DB_PASSWORD', '')
    db_host = os.getenv('PERSONAL_DATA_DB_HOST', 'localhost')
    db_name = os.getenv('PERSONAL_DATA_DB_NAME')

    return mysql.connector.connect(
        user=db_username,
        password=db_password,
        host=db_host,
        database=db_name
    )


def main() -> None:
    """
    Retrieves all rows from the users table
    and logs each row in a filtered format.
    """

    logger = get_logger()
    db_connection = get_db()
    cursor = db_connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users")

    for row in cursor.fetchall():
        message = "; ".join([f"{key}={value}" for key, value in row.items()])
        logger.info(message)

    cursor.close()
    db_connection.close()

if __name__ == "__main__":
    main()
