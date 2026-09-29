from contextlib import contextmanager

import psycopg2
from psycopg2.pool import ThreadedConnectionPool

from config import (
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
    DB_SCHEMA,
    DB_POOL_MIN,
    DB_POOL_MAX,
)
from utils.logger import logger
from database.schema import (
    CREATE_SCHEMA_SQL,
    CREATE_MACHINES_TABLE_SQL,
    CREATE_SENSOR_READINGS_TABLE_SQL,
    CREATE_IMPORT_BATCHES_TABLE_SQL,
    CREATE_MACHINE_TIMESTAMP_INDEX_SQL,
    CREATE_SENSOR_TAG_INDEX_SQL,
    CREATE_TIMESTAMP_INDEX_SQL,
)
class DatabaseError(Exception):
    pass
class ConflictError(DatabaseError):
    pass
class RelatedResourceNotFoundError(DatabaseError):
    pass
class DatabaseManager:
    def __init__(self):
        self.host = DB_HOST
        self.port = DB_PORT
        self.database = DB_NAME
        self.user = DB_USER
        self.password = DB_PASSWORD
        self.schema = DB_SCHEMA
        self._pool = None

    def _ensure_pool(self):
        if self._pool is None:
            try:
                logger.info("Creating PostgreSQL connection pool: min=%s max=%s", DB_POOL_MIN, DB_POOL_MAX)
                self._pool = ThreadedConnectionPool(
                    DB_POOL_MIN,
                    DB_POOL_MAX,
                    host=self.host,
                    port=self.port,
                    database=self.database,
                    user=self.user,
                    password=self.password,
                )
                logger.info("PostgreSQL connection pool created")
            except psycopg2.Error as error:
                raise DatabaseError(
                    f"Database connection pool could not be created: {error}"
                ) from error
        return self._pool

    def close_pool(self):
        if self._pool is not None:
            self._pool.closeall()
            self._pool = None
            logger.info("PostgreSQL connection pool closed")

    @contextmanager
    def connection(self, commit=True):
        pool = self._ensure_pool()
        conn = pool.getconn()
        try:
            yield conn
            if commit:
                conn.commit()
        except BaseException:
            try:
                conn.rollback()
            except psycopg2.Error:
                conn.closed = True
            raise
        finally:
            if conn.closed:
                pool.putconn(conn, close=True)
            else:
                pool.putconn(conn)

    @contextmanager
    def cursor(self, commit=True):
        with self.connection(commit=commit) as conn:
            cursor = conn.cursor()
            try:
                yield cursor
            finally:
                cursor.close()

    def get_connection(self, database=None):
        try:
            return psycopg2.connect(
                host=self.host,
                port=self.port,
                database=database or self.database,
                user=self.user,
                password=self.password,
            )
        except psycopg2.Error as error:
            logger.exception("Database connection failed")
            raise DatabaseError(f"Database connection failed: {error}") from error

    def create_database(self):
        connection = cursor = None
        try:
            connection = self.get_connection("postgres")
            connection.autocommit = True
            cursor = connection.cursor()
            cursor.execute(f"CREATE DATABASE {self.database}")
        except psycopg2.errors.DuplicateDatabase:
            logger.info("Database already exists: %s", self.database)
        except psycopg2.Error as error:
            raise DatabaseError(f"Database creation failed: {error}") from error
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def create_schema(self):
        with self.cursor() as cursor:
            cursor.execute(CREATE_SCHEMA_SQL)
        logger.info("Database schema verified: %s", self.schema)

    def create_tables(self):
        with self.cursor() as cursor:
            cursor.execute(CREATE_MACHINES_TABLE_SQL)
            cursor.execute(CREATE_SENSOR_READINGS_TABLE_SQL)
            cursor.execute(CREATE_IMPORT_BATCHES_TABLE_SQL)
            cursor.execute(CREATE_MACHINE_TIMESTAMP_INDEX_SQL)
            cursor.execute(CREATE_SENSOR_TAG_INDEX_SQL)
            cursor.execute(CREATE_TIMESTAMP_INDEX_SQL)
        logger.info("Database tables and indexes verified: schema=%s", self.schema)

db = DatabaseManager()