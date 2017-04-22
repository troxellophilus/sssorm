from sssorm.model import Model


def connect_database(database_path):
    Model.connect_database(database_path)


def cursor(func):
    def wrapper(cls, *args, **kwargs):
        cls._conn.row_factory = cls._model_factory
        with cls._conn as conn:
            cls.cursor = conn.cursor()
            res = func(cls, *args, **kwargs)
        cls.cursor = None
        return res
    return wrapper
