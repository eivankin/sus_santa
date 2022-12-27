from dataclasses import dataclass
from enum import Enum
from math import sqrt

from dataclass_wizard import JSONWizard, json_field

from phase3.constants import MAX_COORD


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
class Solution(JSONWizard):
    map_id: str = json_field("mapID", all=True)
    # TODO


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
