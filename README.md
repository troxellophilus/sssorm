# Stupid Simple SQLite3 ORM for Python

Tiny simple SQLite3 ORM for Python. Designed for the fastest development from nothing to CRUD-able object, sacrificing some bells and whistles available in other ORMs.

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

Create a Model. Class attributes specify columns and types, while __init__ keyword arguments specify optional default values.

```python
class Person(sssorm.Model):
    name = str
    age = int
    created = datetime.datetime

    def __init__(self, name, age=0, created=datetime.datetime.utcnow, **_kwargs):
        super().__init__(name=name, age=age, created=created, **_kwargs)
```

Insert a record into the table (the table will be created automatically). Note that the created field will be populated by executing the datetime.datetime.utcnow function passed in as default.

```python
person = Person(name='Galadir', age=27)
person.create()
```

Get a record from the table.

```python
person = Person.get_one(name='Galadir')
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
