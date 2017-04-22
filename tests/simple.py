import uuid

import ssorm

ssorm.connect_database('tests/test.db')


def uuid4():
    return str(uuid.uuid4())


class Person(ssorm.Model):
    name = str
    age = int
    uid = (str, 'UNIQUE')

    def __init__(self, name='default', age=0, uid=uuid4, **_kwargs):
        super().__init__(name=name, age=age, uid=uid, **_kwargs)

    @classmethod
    @ssorm.cursor
    def get_22_yos(cls):
        cls.cursor.execute('select * from Person where age=22')
        return cls.cursor.fetchall()


person = Person('Sam', 22)
person.create()

print(Person.get_one(name='Sam'))

print(Person.get_22_yos())

person = Person()
person.create()

print(Person.get_one(name='default'))

