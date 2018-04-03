import datetime

import sssorm

sssorm.connect_database('tests/test.db')


class Person(sssorm.Model):
    name = str
    age = int
    created = datetime.datetime

    def __init__(self, name='default', age=0, created=datetime.datetime.utcnow, **_kwargs):
        super().__init__(name=name, age=age, created=created, **_kwargs)

    @classmethod
    @sssorm.cursor
    def get_22_yos(cls):
        cls.cursor.execute('select * from Person where age=22')
        return cls.cursor.fetchall()

    @property
    @sssorm.cursor
    def tt_yos(self):
        self.cursor.execute('select * from Person where age=22')
        return self.cursor.fetchall()


person = Person('Sam', 22)
person.create()

print(Person.get_one(name='Sam'))

print(Person.get_22_yos())

person = Person()
person.create()

print(Person.get_one(name='default'))

print(person.tt_yos)

