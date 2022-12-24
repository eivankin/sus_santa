from dataclasses import dataclass
from dataclass_wizard import JSONWizard, json_field
from math import sqrt, cos, sin, pi

from shapely.geometry import LineString
from shapely.geometry import Point

Bag = list[int]


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
        return self.dist(circle.center) <= circle.radius

    def __add__(self, other: "Coordinates") -> "Coordinates":
        return Coordinates(self.x + other.x, self.y + other.y)

    def __mul__(self, other: int) -> "Coordinates":
        return Coordinates(self.x * other, self.y * other)

    def __sub__(self, other: "Coordinates") -> "Coordinates":
        return self + (other * -1)

    def vector_dot(self, other: "Coordinates") -> int:
        return self.x * other.x + self.y * other.y


@dataclass
class Circle:
    center: Coordinates
    radius: int

    @classmethod
    def from_snow(cls, snow: "SnowArea"):
        return cls(center=Coordinates(snow.x, snow.y), radius=snow.r)


@dataclass
class Route(JSONWizard):
    moves: list[Coordinates]
    stack_of_bags: list[Bag] = json_field("stackOfBags", all=True)
    map_id: str = json_field("mapID", all=True)


@dataclass
class RouteResponse(JSONWizard):
    success: bool
    error: str
    round_id: str


@dataclass
class RouteData(JSONWizard):
    error_message: str
    status: str
    total_time: int
    total_length: int


@dataclass
class RoundInfo(JSONWizard):
    success: bool
    error: str
    data: RouteData


@dataclass
class Gift(JSONWizard):
    id: int
    weight: int
    volume: int


@dataclass
class SnowArea(JSONWizard):
    r: int
    x: int
    y: int


@dataclass
class Map(JSONWizard):
    gifts: list[Gift]
    children: list[Coordinates]
    snow_areas: list[SnowArea] = json_field("snowAreas", all=True)


@dataclass
class BagDescription:
    weight: int
    volume: int

    @classmethod
    def from_bag(cls, map_data: Map, bag: Bag):
        gifts = [gift for gift in map_data.gifts if gift.id in bag]
        return cls(
            weight=sum(g.weight for g in gifts), volume=sum(g.volume for g in gifts)
        )


@dataclass
class Line:
    """Equation of the line in format 'ax + by + c = 0'"""

    from_pos: Coordinates
    to_pos: Coordinates

    a: float
    b: float
    c: float

    @classmethod
    def from_two_points(cls, from_pos: Coordinates, to_pos: Coordinates):
        dx = to_pos.x - from_pos.x
        dy = to_pos.y - from_pos.y
        k = dy / dx if dx else 0
        b = to_pos.y - to_pos.x * k
        return cls(from_pos=from_pos, to_pos=to_pos, a=-k, b=1, c=-b)

    def distance_in_circle(self, circle: "Circle") -> float:
        c = Point(circle.center.x, circle.center.y)
        c = c.buffer(circle.radius)
        l = LineString(
            [(self.from_pos.x, self.from_pos.y), (self.to_pos.x, self.to_pos.y)]
        )
        intersection = l.intersection(c)
        length = intersection.length
        assert length != 0 or intersection.is_empty
        return length


@dataclass
class EmulatorReportSegment(JSONWizard):
    from_pos: Coordinates
    to_pos: Coordinates
    distance: float
    distances_in_snow: list[float]


@dataclass
class EmulatorReport(JSONWizard):
    total_distance: float
    distance_in_snow: float
    segments: list[EmulatorReportSegment]
