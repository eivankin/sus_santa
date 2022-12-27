from dataclasses import dataclass
from enum import Enum
from math import sqrt, pi, cos, sin

from dataclass_wizard import JSONWizard, json_field

from phase3.constants import MAX_COORD

Bag = list[int]
Matrix = list[list[float]]


@dataclass
class Circle:
    center: 'Coordinates'
    radius: int

    @classmethod
    def from_snow(cls, snow: "SnowArea"):
        return cls(center=Coordinates(snow.x, snow.y), radius=snow.r)

    def get_outer_points(self) -> list['Coordinates']:
        num_vertices = 8
        angle_step = 2 * pi / num_vertices
        cos_a = cos(angle_step)
        sin_a = sin(angle_step)
        hypot = self.radius / cos(angle_step / 2)
        ds = [Coordinates(hypot, 0)]
        for _ in range(num_vertices - 1):
            (x, y) = (ds[-1].x, ds[-1].y)
            ds.append(Coordinates(x * cos_a - y * sin_a, x * sin_a + y * cos_a))

        result = []
        for dc in ds:
            c = self.center + dc
            if c.in_bounds():
                result.append(c.round())
        return result


@dataclass
class Map(JSONWizard):
    gifts: list['Gift']
    children: list['Child']
    snow_areas: list['SnowArea'] = json_field('snowArea', all=True)


@dataclass
class Gift(JSONWizard):
    id: int
    type: str
    price: int
    weight: int
    volume: int

    def compact(self):
        return f"Gift(id:{self.id:4}, {self.type:21}, price:{self.price:3})"

    def as_tuple(self) -> tuple[int, str, int, int, int]:
        return self.id, self.type, self.price, self.weight, self.volume

    def __eq__(self, other: "Gift"):
        return self.as_tuple() == other.as_tuple()

    def __hash__(self):
        return hash(self.as_tuple())


@dataclass
class SnowArea(JSONWizard):
    r: int
    x: int
    y: int


@dataclass
class Child(JSONWizard):
    gender: str
    age: int
    x: int
    y: int

    def compact(self):
        return f"Child({self.gender:6}, age:{self.age:2})"

    def coords(self):
        return Coordinates(self.x, self.y)


@dataclass
class Coordinates(JSONWizard):
    x: int
    y: int

    def dist(self, to: "Coordinates") -> float:
        """Euclidean distance to other coordinates"""
        return sqrt((self.x - to.x) ** 2 + (self.y - to.y) ** 2)

    def __eq__(self, other: "Coordinates") -> bool:
        return (self.x, self.y) == (other.x, other.y)

    def __hash__(self):
        return hash((self.x, self.y))

    def in_circle(self, circle: "Circle") -> bool:
        return self.dist(circle.center) < circle.radius

    def __add__(self, other: "Coordinates") -> "Coordinates":
        return Coordinates(self.x + other.x, self.y + other.y)

    def __mul__(self, other: int) -> "Coordinates":
        return Coordinates(self.x * other, self.y * other)

    def __sub__(self, other: "Coordinates") -> "Coordinates":
        return self + (other * -1)

    def vector_dot(self, other: "Coordinates") -> int:
        return self.x * other.x + self.y * other.y

    @classmethod
    def from_str(cls, s: str) -> "Coordinates":
        return cls(*map(int, s.split()))

    def to_str(self):
        return f"{self.x} {self.y}"

    def in_bounds(self):
        return 0 <= self.x <= MAX_COORD and 0 <= self.y <= MAX_COORD

    def round(self):
        return Coordinates(round(self.x), round(self.y))

@dataclass
class Present(JSONWizard):
    gift_id: int = json_field("giftID", all=True)
    child_id: int = json_field("childID", all=True)


@dataclass
class Solution(JSONWizard):
    moves: list[Coordinates]
    stack_of_bags: list[Bag] = json_field("stackOfBags", all=True)
    map_id: str = json_field("mapID", all=True)


@dataclass
class SolutionResponse(JSONWizard):
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


class Gender(Enum):
    MALE = "male"
    FEMALE = "female"


class Category(Enum):
    EDUCATIONAL_GAMES = "educational_games"
    BATH_TOYS = "bath_toys"
    MUSIC_GAMES = "music_games"
    TOY_KITCHEN = "toy_kitchen"
    BIKE = "bike"
    PAINTS = "paints"
    CASKET = "casket"
    SOCCER_BALL = "soccer_ball"