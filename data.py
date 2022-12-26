from dataclasses import dataclass

import numba
from dataclass_wizard import JSONWizard, json_field
from math import sqrt, ceil

from shapely.geometry import LineString
from shapely.geometry import Point

from constants import MAX_COORD

Bag = list[int]
Matrix = list[list[float]]


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


@dataclass
class Circle:
    center: Coordinates
    radius: int

    @classmethod
    def from_snow(cls, snow: "SnowArea"):
        return cls(center=Coordinates(snow.x, snow.y), radius=snow.r)

    def get_outer_points(self) -> list[Coordinates]:
        delta = ceil(sqrt(2 * self.radius**2))
        ds = [
            (0, delta),
            (delta, 0),
            (-delta, 0),
            (0, -delta),
            (0, self.radius),
            (self.radius, 0),
            (-self.radius, 0),
            (0, -self.radius),
        ]

        result = []
        for (dx, dy) in ds:
            c = Coordinates(self.center.x + dx, self.center.y + dy)
            if c.in_bounds():
                result.append(c)
        return result


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
class Path(JSONWizard):
    path: list[Coordinates]
    length: float


@numba.njit
def in_circle(x, y, cx, cy, r):
    return (x - cx) ** 2 + (y - cy) ** 2 < r**2


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

    def distance_in_circle(self, circle: "Circle", use_old=False) -> float:
        if use_old:
            c = Point(circle.center.x, circle.center.y)
            c = c.buffer(circle.radius)
            l = LineString(
                [(self.from_pos.x, self.from_pos.y), (self.to_pos.x, self.to_pos.y)]
            )
            intersection = l.intersection(c)
            length = intersection.length
            return length

        return Line._distance_in_circle(
            self.from_pos.x,
            self.from_pos.y,
            self.to_pos.x,
            self.to_pos.y,
            circle.center.x,
            circle.center.y,
            circle.radius,
        )

    @staticmethod
    @numba.njit
    def _distance_in_circle(p1x, p1y, p2x, p2y, cx, cy, r):
        p1_in, p2_in = in_circle(p1x, p1y, cx, cy, r), in_circle(p2x, p2y, cx, cy, r)
        if p1_in and p2_in:
            return ((p1x - p2x) ** 2 + (p1y - p2y) ** 2) ** 0.5

        (x1, y1), (x2, y2) = (p1x - cx, p1y - cy), (p2x - cx, p2y - cy)
        dx, dy = (x2 - x1), (y2 - y1)
        dr = (dx**2 + dy**2) ** 0.5
        big_d = x1 * y2 - x2 * y1
        discriminant = r**2 * dr**2 - big_d**2

        if discriminant <= 0:
            return 0

        intersections = [
            (
                cx
                + (big_d * dy + sign * (-1 if dy < 0 else 1) * dx * discriminant**0.5)
                / dr**2,
                cy + (-big_d * dx + sign * abs(dy) * discriminant**0.5) / dr**2,
            )
            for sign in ((1, -1) if dy < 0 else (-1, 1))
        ]  # This makes sure the order along the segment is correct
        fraction_along_segment = [
            (xi - p1x) / dx if abs(dx) > abs(dy) else (yi - p1y) / dy
            for xi, yi in intersections
        ]
        intersections = [
            pt
            for pt, frac in zip(intersections, fraction_along_segment)
            if 0 <= frac <= 1
        ]

        if p1_in:
            intersections.append((p1x, p1y))
        if p2_in:
            intersections.append((p2x, p2y))

        if len(intersections) < 2:
            return 0

        (x1, y1), (x2, y2) = intersections
        return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5


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


if __name__ == "__main__":
    line = Line.from_two_points(Coordinates(617, 568), Coordinates(539, 715))
    print(line.distance_in_circle(Circle(Coordinates(432, 939), 303)))
