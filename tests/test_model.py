from datetime import datetime
import os
import unittest

from sssorm import Model


_DB = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'test.db')


class Person(Model):

    name = (str, 'default')
    age = int
    cakes = (int, 0)
    networth = (float, 0.0)
    data = (bytes, b'{"key": "value"}')
    created = (datetime, datetime.utcnow)


class Player(Model):

    person = Person
    number = int
    position = str


class TestModel(unittest.TestCase):

    def setUp(self):
        Model.connect_database(_DB)

    def tearDown(self):
        Model._conn.close()
        os.remove(_DB)

    def test_init(self):
        person = Person()
        self.assertEqual(person.name, 'default')
        self.assertIsNone(person.age)
        self.assertEqual(person.cakes, 0)
        self.assertEqual(person.networth, 0.0)
        self.assertIsInstance(person.created, datetime)
        self.assertEqual(person.data, b'{"key": "value"}')
        self.assertIsNone(person.idx)

    def test_schema(self):
        self.assertDictEqual(
            dict(Person.schema()),
            {
                '_idx': 'INTEGER PRIMARY KEY',
                'name': 'TEXT',
                'age': 'INTEGER',
                'cakes': 'INTEGER',
                'networth': 'REAL',
                'data': 'BLOB',
                'created': 'TIMESTAMP'
            }
        )

    def test_create(self):
        person = Person()
        person.create()
        self.assertEqual(person.name, 'default')
        self.assertIsNone(person.age)
        self.assertEqual(person.cakes, 0)
        self.assertEqual(person.networth, 0.0)
        self.assertIsInstance(person.created, datetime)
        self.assertEqual(person.data, b'{"key": "value"}')
        self.assertIsInstance(person.idx, int)

    def test_get_by_index(self):
        person_a = Person()
        person_a.create()
        person_b = Person.get_by_index(person_a.idx)
        self.assertEqual(person_a, person_b)

    def test_get_one(self):
        person_a = Person()
        person_a.create()
        person_b = Person(name='dave', age=30, cakes=1)
        person_b.create()
        self.assertEqual(person_b, Person.get_one())
        self.assertEqual(person_a, Person.get_one(name='default'))
        self.assertEqual(person_b, Person.get_one(name='dave'))
        self.assertEqual(person_a, Person.get_one(cakes=0))
        self.assertEqual(person_b, Person.get_one(cakes=1, age=30))

    def test_get_many(self):
        person_a = Person()
        person_a.create()
        person_b = Person(name='dave', age=30, cakes=1)
        person_b.create()
        person_c = Person(name='sally', age=40, cakes=5)
        person_c.create()
        people = Person.get_many()
        self.assertListEqual(list(people), [person_c, person_b, person_a])
        people = Person.get_many(name='dave')
        self.assertListEqual(list(people), [person_b])

    def test_update(self):
        person = Person()
        person.create()
        person.name = 'stan'
        person.age = 12
        person.cakes = 10
        person.update()
        updated = Person.get_by_index(person.idx)
        self.assertEqual(person, updated)

    def test_delete(self):
        person = Person()
        person.create()
        person.delete()
        self.assertEqual(len(list(Person.get_many())), 0)
    
    def test_foreign_key(self):
        person = Person()
        person.create()
        player = Player(person=person, number=22, position='P')
        player.create()
        person = Person.get_by_index(person.idx)
        player = Player.get_by_index(player.idx)
        self.assertEqual(person, player.person)

    def test_null_foreign_key(self):
        player = Player(number=22, position='P')
        player.create()
        player = Player.get_by_index(player.idx)
        self.assertIsNone(player.person)


if __name__ == '__main__':
    unittest.main()
