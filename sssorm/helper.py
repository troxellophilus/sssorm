import sqlite3

from sssorm.model import Model


def connect_database(database_path, detect_types=sqlite3.PARSE_DECLTYPES):
    Model.connect_database(database_path, detect_types or 0)


def cursor(func):
    def wrapper(cls, *args, **kwargs):
        cls._conn.row_factory = sqlite3.Row
        with cls._conn as conn:
            cls._cursor = conn.cursor()
            row = func(cls, *args, **kwargs)
        cls._cursor = None
        return row
    return wrapper
