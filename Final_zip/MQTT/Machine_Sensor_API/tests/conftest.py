"""Shared fixtures: a real app object with no live database behind it.

The database seam is `database.connection.db` (the pool singleton). Services
and the health check all reference this module-level instance, so replacing
`app_module.db` with a fake before create_app() runs isolates every test from
PostgreSQL while still exercising the real route/service/handler code paths.
"""
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database import connection as db_module


class FakeCursor:
    """Scriptable stand-in for a pooled psycopg2 cursor."""

    def __init__(self, results=None, rowcount=0, fail_with=None):
        self._results = list(results or [])
        self.rowcount = rowcount
        self._fail_with = fail_with
        self.executed = []

    def execute(self, query, values=None):
        self.executed.append((query, values))
        if self._fail_with is not None:
            raise self._fail_with

    def fetchone(self):
        return self._results.pop(0) if self._results else None

    def fetchall(self):
        rows, self._results = self._results, []
        return rows

    def close(self):
        pass


class FakeDB:
    """Stands in for DatabaseManager at the service seam."""

    schema = "machine_schema"

    def __init__(self):
        self.cursor_stack = []
        self.fail_on_execute = None
        self.all_queries = []

    def push_cursor(self, cursor):
        self.cursor_stack.append(cursor)

    def _next_cursor(self):
        cursor = self.cursor_stack.pop(0) if self.cursor_stack else FakeCursor()
        cursor._fail_with = self.fail_on_execute
        self.all_queries.append("(no execute)")
        original_execute = cursor.execute

        def recording_execute(query, values=None):
            self.all_queries[-1] = query
            return original_execute(query, values)

        cursor.execute = recording_execute
        return cursor

    def cursor(self, commit=True):
        import contextlib

        @contextlib.contextmanager
        def _ctx():
            yield self._next_cursor()

        return _ctx()

    def connection(self, commit=True):
        import contextlib

        @contextlib.contextmanager
        def _ctx():
            yield None

        return _ctx()

    def get_connection(self, database=None):
        raise db_module.DatabaseError("no live database in tests")


@pytest.fixture()
def fake_db():
    return FakeDB()


@pytest.fixture()
def client(fake_db, monkeypatch):
    """The real app with the pool swapped for FakeDB everywhere.

    Services and the health check do `from database.connection import db`,
    which binds the pool singleton into each module at import time. Patching
    only app_module.db would leave the services on the live pool — so the
    fake replaces the name in every module that holds a reference.
    """
    import app as app_module
    from services import machine_service, pickle_importer, reading_service

    for module in (
        app_module,
        machine_service,
        reading_service,
        pickle_importer,
    ):
        monkeypatch.setattr(module, "db", fake_db)

    application = app_module.create_app()
    application.config["TESTING"] = True
    return application.test_client()
