# Somewhat Small SQLite3 ORM for Python

Small SQLite3 ORM for Python. Move quickly from from nothing to CRUD-able object, sacrificing some bells and whistles available in other ORMs.

## Install

```bash
$ git clone git@gitlab.com:dtrox/sssorm.git
$ cd sssorm
$ pip install .
```

## Getting Started

Import sssorm.

```python
import sssorm
```

Connect a database.

```python
sssorm.connect_database('example.db')
```

Create a Model. To define a model, create a class that inherits from Model and declare the schema via class attributes. Each attribute can either be a type or a tuple of a type and a default value. Python primitive types, date/datetime, and models are all supported by default; any additional types must be correctly registered via sqlite3 adapters/converters.

Default values can be set to functions, in which case the function is called to create the default value.

This ORM is very opinionated: for all Model objects, a monotonically increasing primary key field 'idx' is automatically created and all fields except for the key are considered nullable. The primary key can be accessed from instantiated models via the .idx property.

```python
from datetime import datetime

class Person(sssorm.Model):

    name = (str, 'default')  # Field 'name' has type 'str' and default value 'default'.
    age = int  # Field 'age' has type 'int' and no default value.
    cakes = (int, 0)
    networth = (float, 0.0)
    data = (bytes, b'{"key": "value"}')
    created = (datetime, datetime.utcnow)  # Field 'created' has type 'datetime' and default value the result of calling datetime.utcnow.
```

Insert a record into the table. The table will be created automatically if it does not exist (this occurs for any database action with the Model). Note that the created field will be populated by executing the datetime.datetime.utcnow function passed in as default.

```python
person = Person(name='Galadir', age=27)
person.create()
```

Get a record from the table. All getter methods support arbitrary keyword arguments for WHERE clause matching.

```python
person = Person.get_one(name='Galadir')  # Retrieve one Person with name == 'Galadir' from the database.
```

Update a record in the table.

```python
person.age += 1
person.update()
```

Delete a record in the table.

```python
person.delete()
```

## More Details

TODO

## Alternatives

* PeeWee: http://docs.peewee-orm.com/en/latest/
* SQLAlchemy: http://docs.sqlalchemy.org/en/latest/index.html

## License

MIT License

Copyright (c) 2018 Drew Troxell
