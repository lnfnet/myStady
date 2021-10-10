class Gun(object):
    def __init__(self) -> None:
        self.name = '98K'
        self.attack = 888

class Player(object):
    def __init__(self) -> None:
        self.weapon = Gun()

Jack = Player()
print(Jack.weapon.name)
print(Jack.weapon.attack)
