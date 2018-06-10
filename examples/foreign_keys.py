from sssorm import Model


Model.connect_database('example.db')


class Person(Model):

    firstname = str
    lastname = str
    age = int


class Player(Model):

    person = Person
    number = int
    position = str


person = Person(firstname="Chris", lastname="Taylor", age=27)
person.create()

_ = Player(person=person, number=3, position='SS').create()

player = Player.get_one()
print(player)
print(player.person)
