import sqlite3


def cursor(func):
    def wrapper(cls, *args, **kwargs):
        cls._conn.row_factory = cls._model_factory
        with cls._conn as conn:
            cls._cursor = conn.cursor()
            try:
                row = func(cls, *args, **kwargs)
            except sqlite3.OperationalError as err:
                if 'no such table' in str(err):
                    cls.create_table()
                    row = func(cls, *args, **kwargs)
                else:
                    raise
        cls._cursor = None
        return row
    return wrapper
