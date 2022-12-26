from dataclasses import dataclass
from enum import Enum

from dataclass_wizard import JSONWizard, json_field


@dataclass
class Gift(JSONWizard):
    id: int
    type: str
    price: int

    def compact(self):
        return f"Gift(id:{self.id:4}, {self.type:15}, price:{self.price})"

    def as_tuple(self) -> tuple[int, str, int]:
        return self.id, self.type, self.price

    def __eq__(self, other: 'Gift'):
        return self.as_tuple() == other.as_tuple()

    def __hash__(self):
        return hash(self.as_tuple())


@dataclass
class Child(JSONWizard):
    id: int
    gender: str
    age: int

    def compact(self):
        return f"Child(id:{self.id:4}, {self.gender:6}, age:{self.age:2})"


@dataclass
class Map(JSONWizard):
    gifts: list[Gift]
    children: list[Child]


# Order classes

@dataclass
class Present(JSONWizard):
    gift_id: int = json_field("giftID", all=True)
    child_id: int = json_field("childID", all=True)


@dataclass
class Order(JSONWizard):
    map_id: str = json_field("mapID", all=True)
    presenting_gifts: list[Present] = json_field("presentingGifts", all=True)


@dataclass
class OrderResponse(JSONWizard):
    success: bool
    error: str
    round_id: str


# Status classes

@dataclass
class RoundInfoData(JSONWizard):
    error_message: str = json_field("error_message")
    status: str = json_field("status")
    total_happy: int = json_field("total_happy")


@dataclass
class RoundInfo(JSONWizard):
    success: bool
    error: str
    data: RoundInfoData


class Category(Enum):
    CONSTRUCTORS = 'constructors'
    DOLLS = 'dolls'
    RADIO_CONTROLLED_TOYS = 'radio_controlled_toys'
    TOY_VEHICLES = 'toy_vehicles'
    BOARD_GAMES = 'board_games'
    OUTDOOR_GAMES = 'outdoor_games'
    PLAYGROUND = 'playground'
    SOFT_TOYS = 'soft_toys'
    COMPUTER_GAMES = 'computer_games'
    SWEETS = 'sweets'
    BOOKS = 'books'
    PET = 'pet'
    CLOTHES = 'clothes'


class Gender(Enum):
    MALE = 'male'
    FEMALE = 'female'
