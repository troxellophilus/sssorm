import sqlite3

from sssorm.model import Model


def connect_database(database_path, detect_types=sqlite3.PARSE_DECLTYPES):
    Model.connect_database(database_path, detect_types or 0)


def cursor(func):
    def wrapper(cls, *args, **kwargs):
        cls._conn.row_factory = cls._model_factory
        with cls._conn as conn:
            cls._cursor = conn.cursor()
            res = func(cls, *args, **kwargs)
        cls._cursor = None
        return res
    return wrapper
