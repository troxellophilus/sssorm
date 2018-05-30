"""Database models."""

import datetime
import inspect
import logging
import sqlite3

import enum


def _sqltype(obj):
    if obj == str or isinstance(obj, str):
        sql_type = 'TEXT'
    elif (
        obj == int
        or obj == bool
        or isinstance(obj, (int, bool))
    ):
        sql_type = 'INTEGER'
    elif obj == float or isinstance(obj, float):
        sql_type = 'REAL'
    elif obj == bytes or isinstance(obj, bytes):
        sql_type = 'BLOB'
    elif obj == datetime.datetime or isinstance(obj, datetime.datetime):
        sql_type = 'TIMESTAMP'
    elif obj == datetime.date or isinstance(obj, datetime.date):
        sql_type = 'DATE'
    elif isinstance(obj, Model):
        sql_type = obj.__class__.__name__
    elif isinstance(obj, type) and issubclass(obj, Model):
        sql_type = obj.__name__
    else:
        raise TypeError('Unrecognized type: {}, {}'.format(obj, type(obj)))
    return sql_type


class Model(object):
    """A parent for DB models."""

    _idx = None
    _conn = None  # type: sqlite3.Connection
    _cursor = None  # type: sqlite3.Cursor
    _converters = {}

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
            if not hasattr(self, col) or inspect.isroutine(vars(self).get(col)):
                raise AttributeError("Model '{}' has no column with name '{}'.".format(self.__class__.__name__, col))
            value = val() if callable(val) else val
            setattr(self, col, value)

    @classmethod
    def connect_database(cls, db_path):
        cls._conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)

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

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and other.idx == self.idx
            and all(vars(other)[k] == v for k, v in self.items())
        )

    def __repr__(self):
        kwargs = ', '.join("{}={}".format(k, repr(v)) for k, v in self.items())
        return '{}({})'.format(type(self).__name__, kwargs)

    def __conform__(self, protocol):
        if protocol is sqlite3.PrepareProtocol:
            return self.idx

    @classmethod
    def _model_factory(cls, cursor, row):
        row = sqlite3.Row(cursor, row)
        return cls(**row)

    def items(self):
        attrs = vars(self)
        return tuple((c, attrs[c]) for c in self.columns())

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
        schema = [('_idx', 'INTEGER PRIMARY KEY')]
        for col, value in filter(lambda m: not m[0].startswith('_'), class_attrs):
            if isinstance(value, (tuple, list)):
                sql_type = _sqltype(value[0])
            else:
                sql_type = _sqltype(value)
            schema.append((col, sql_type))
            # Register converters/adapters if necessary
            if isinstance(value, Model) or (isinstance(value, type) and issubclass(value, Model)):
                if sql_type not in cls._converters:
                    if isinstance(value, Model):
                        converter = lambda s: type(value).get_by_index(int(s))
                    else:
                        parent = inspect.getmro(value)[0]
                        converter = lambda s: parent.get_by_index(int(s))
                    cls._converters[sql_type] = converter
                    sqlite3.register_converter(sql_type, converter)
        return tuple(schema)

    @classmethod
    def columns(cls):
        return filter(lambda c: c != '_idx', map(lambda t: t[0], cls.schema()))

    @classmethod
    def create_table(cls):
        """Create the table."""
        columns = []
        for col, type_str in cls.schema():
            col_def = '{} {}'.format(col, type_str)
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
            try:
                sql_type = _sqltype(val)
            except TypeError:
                items[col] = val if val is None else int(val)
            else:
                if sql_type == 'INTEGER':
                    items[col] = int(val)
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
    def get_by_index(cls, idx):
        cls._conn.row_factory = cls._model_factory
        select = '''SELECT * FROM {} WHERE _idx=?;'''.format(cls.__name__)
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
        select = '''SELECT * FROM {} {} ORDER BY _idx DESC;'''.format(cls.__name__, where)
        with cls._conn:
            curs = cls._conn.cursor()
            curs.execute(select, params)
            return curs.fetchone()

    @classmethod
    def get_many(cls, limit=None, **params):
        """Retrieve objects from the table."""
        cls._conn.row_factory = cls._model_factory
        lim = " LIMIT {}".format(limit) if limit else ''
        if params:
            where = ' and '.join('=:'.join((k, k)) for k in params)
            select = '''SELECT * FROM {} WHERE {}{};'''.format(cls.__name__, where, lim)
        else:
            select = '''SELECT * FROM {} {} ORDER BY _idx DESC;'''.format(cls.__name__, lim)
        with cls._conn:
            curs = cls._conn.cursor()
            curs.execute(select, params)
            return curs.fetchmany(limit) if limit else curs.fetchall()

    def update(self):
        """Update this record in the table with its current values."""
        new_vals = ', '.join('=:'.join((k, k)) for k in self.columns())
        query = '''UPDATE {} SET {} WHERE _idx={};'''.format(type(self).__name__, new_vals, self.idx)
        with self._conn:
            curs = self._conn.cursor()
            curs.execute(query, dict(self.items()))

    def delete(self):
        """Remove this record from the table."""
        delete_stmnt = '''DELETE FROM {} WHERE _idx={}'''.format(type(self).__name__, self.idx)
        with self._conn:
            curs = self._conn.cursor()
            curs.execute(delete_stmnt)
