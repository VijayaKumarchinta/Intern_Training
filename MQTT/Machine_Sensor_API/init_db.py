import sys

from database.connection import db, DatabaseError
from utils.logger import logger

def main():
    try:
        db.create_database()
        db.create_schema()
        db.create_tables()
    except DatabaseError as error:
        logger.exception("Database initialization failed: %s", error)
        return 1

    logger.info("Database initialization complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())