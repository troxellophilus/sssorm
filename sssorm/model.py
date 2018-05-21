"""Database models."""

import datetime
import inspect
import logging
import sqlite3

import enum


def _sqltype(obj):
    if obj == str or isinstance(obj, str) or isinstance(obj, enum.Enum):
        sql_type = 'TEXT'
    elif obj == int or obj == bool or isinstance(obj, (int, bool)):
        sql_type = 'INTEGER'
    elif obj == float or isinstance(obj, float):
        sql_type = 'REAL'
    elif obj == bytes or isinstance(obj, bytes):
        sql_type = 'BLOB'
    elif obj == datetime.datetime or isinstance(obj, datetime.datetime):
        sql_type = 'TIMESTAMP'
    elif obj == datetime.date or isinstance(obj, datetime.date):
        sql_type = 'DATE'
    else:
        raise TypeError('Unrecognized type: {}, {}'.format(obj, type(obj)))
    return sql_type


class Model(object):
    """A parent for DB models."""

    _conn = None  # type: sqlite3.Connection
    _cursor = None  # type: sqlite3.Cursor

    def __init__(self, **params):
        """Initialize a Model."""
        for col, value in self.__class__.defaults():
            if inspect.isclass(value):
                default_value = None
            elif callable(value):
                default_value = value()
            else:
                default_value = value
            setattr(self, col, default_value)
        for col, val in params.items():
            if not hasattr(self, col):
                if col == 'idx':
                    self._idx = val
                else:
                    raise AttributeError("Model '{}' has no column with name '{}'.".format(self.__class__.__name__, col))
                continue
            value = val() if callable(val) else val
            setattr(self, col, value)

    @classmethod
    def connect_database(cls, db_path, detect_types=sqlite3.PARSE_DECLTYPES):
        cls._conn = sqlite3.connect(db_path, detect_types=detect_types or 0)

    @property
    def idx(self):
        """Index of the object."""
        return self._idx

    def __int__(self):
        return self.idx

    def __index__(self):
        return self.idx

    def __iter__(self):
        return (k for k in vars(self) if not k.startswith('_'))

    def __repr__(self):
        kwargs = ', '.join("{}={}".format(k, repr(v)) for k, v in self.items())
        return '{}({})'.format(type(self).__name__, kwargs)

    def items(self):
        return tuple(t for t in vars(self).items() if not t[0].startswith('_'))

    @classmethod
    def defaults(cls):
        class_attrs = inspect.getmembers(cls, lambda m: not (inspect.isroutine(m) or isinstance(m, property)))
        defaults = []
        for col, value in filter(lambda m: not m[0].startswith('_'), class_attrs):
            if isinstance(value, (tuple, list)):
                defaults.append((col, value[1]))
            else:
                try:
                    _ = _sqltype(value)
                    defaults.append((col, value))
                except TypeError:
                    defaults.append((col, None))
        return defaults

    @classmethod
    def schema(cls):
        class_attrs = inspect.getmembers(cls, lambda m: not (inspect.isroutine(m) or isinstance(m, property)))
        schema = []
        for col, value in filter(lambda m: not m[0].startswith('_'), class_attrs):
            if isinstance(value, (tuple, list)):
                schema.append((col, _sqltype(value[0])))
            else:
                schema.append((col, _sqltype(value)))
        return tuple(schema)

    @classmethod
    def columns(cls):
        return map(lambda t: t[0], cls.schema())

    @classmethod
    def create_table(cls):
        """Create the table."""
        columns = ['idx INTEGER PRIMARY KEY']
        print(list(cls.schema()))
        for col, val in cls.schema():
            print(col, val)
            col_def = '{} {}'.format(col, _sqltype(val))
            columns.append(col_def)
        create = 'CREATE TABLE IF NOT EXISTS %s (%s);' % (
            cls.__name__, ', '.join(columns))
        with cls._conn as conn:
            curs = conn.cursor()
            curs.execute(create)

    def create(self):
        """Insert this object into the table as a new record."""
        names = ', '.join(self.columns())
        values = ', '.join(':{}'.format(k) for k in self.columns())
        insert = '''INSERT INTO {} ({}) VALUES ({});'''.format(
            type(self).__name__, names, values)
        items = dict(self.items())
        for col, val in items.items():
            if isinstance(val, enum.Enum):
                items[col] = val.name
            try:
                _sqltype(val)
            except TypeError:
                items[col] = val if val is None else int(val)
        try:
            with self._conn:
                curs = self._conn.cursor()
                curs.execute(insert, dict(items))
                self._idx = curs.lastrowid
        except sqlite3.OperationalError as err:
            if 'no such table' in str(err):
                self.__class__.create_table()
                with self._conn as conn:
                    curs = conn.cursor()
                    curs.execute(insert, dict(items))
                    self._idx = curs.lastrowid
            else:
                raise err

    @classmethod
    def _model_factory(cls, cursor, row):
        row_dict = {}
        for idx, col in enumerate(cursor.description):
            col_name = col[0]
            if col_name.endswith('_idx'):
                col_name = col_name[:-4]
            row_dict[col_name] = row[idx]
        return cls(**row_dict)

    @classmethod
    def get_by_index(cls, idx):
        cls._conn.row_factory = cls._model_factory
        select = '''SELECT * FROM {} WHERE idx=?;'''.format(cls.__name__)
        with cls._conn:
            curs = cls._conn.cursor()
            curs.execute(select, (idx, ))
            return curs.fetchone()

    @classmethod
    def get_one(cls, **params):
        cls._conn.row_factory = cls._model_factory
        if params:
            where = ' WHERE ' + ' and '.join('=:'.join((k, k)) for k in params)
        else:
            where = ''
        select = '''SELECT * FROM {} {} ORDER BY idx DESC;'''.format(cls.__name__, where)
        with cls._conn:
            curs = cls._conn.cursor()
            curs.execute(select, params)
            return curs.fetchone()

    @classmethod
    def get_many(cls, limit=None, **params):
        """Retrieve objects from the table."""
        cls._conn.row_factory = cls._model_factory
        where = ' and '.join('=:'.join((k, k)) for k in params)
        lim = " LIMIT {}".format(limit) if limit else ''
        select = '''SELECT * FROM {} WHERE {}{};'''.format(cls.__name__, where, lim)
        with cls._conn:
            curs = cls._conn.cursor()
            curs.execute(select, params)
            return curs.fetchmany(limit) if limit else curs.fetchall()

    def update(self):
        """Update this record in the table with its current values."""
        new_vals = ', '.join('=:'.join((k, k)) for k in self.columns())
        query = '''UPDATE {} SET {} WHERE idx={};'''.format(type(self).__name__, new_vals, self.idx)
        with self._conn:
            curs = self._conn.cursor()
            curs.execute(query, dict(self.items()))

    def delete(self):
        """Remove this record from the table."""
        delete_stmnt = '''DELETE FROM {} WHERE idx={}'''.format(type(self).__name__, self.idx)
        with self._conn:
            curs = self._conn.cursor()
            curs.execute(delete_stmnt)
