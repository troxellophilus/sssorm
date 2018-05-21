from datetime import datetime

import sssorm

sssorm.connect_database('tests/test.db')


class Person(sssorm.Model):

    name = 'default'
    age = int
    created = (datetime, datetime.utcnow)

    @classmethod
    @sssorm.cursor
    def get_22_yos(cls):
        cls._cursor.execute('select * from Person where age=22')
        return cls._cursor.fetchall()

    @property
    @sssorm.cursor
    def tt_yos(self):
        self._cursor.execute('select * from Person where age=22')
        return self._cursor.fetchall()


person = Person(name='Sam', age=22)
person.create()

print(Person.get_one(name='Sam'))

print(Person.get_22_yos())

person = Person()
person.create()

print(Person.get_one(name='default'))

print(person.tt_yos)

print(vars(Person.get_one(name='Sam')))
