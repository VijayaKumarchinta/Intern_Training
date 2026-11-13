from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from server.config import (
    DATABASE_URL,
    DB_POOL_SIZE,
    DB_MAX_OVERFLOW,
    DB_POOL_TIMEOUT,
)

engine: Engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=DB_POOL_SIZE,
    max_overflow=DB_MAX_OVERFLOW,
    pool_timeout=DB_POOL_TIMEOUT,
    pool_recycle=1800,
    echo=False,
)


def check_database_connection() -> dict:
    with engine.connect() as connection:
        result = connection.execute(
            text(
                """
                SELECT
                    current_user AS database_user,
                    current_database() AS database_name,
                    current_schema() AS current_schema,
                    version() AS database_version
                """
            )
        ).mappings().one()

        return dict(result)


def ping_database() -> None:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
