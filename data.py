from dataclasses import dataclass
from dataclass_wizard import JSONWizard

Bag = list[int]


@dataclass
class Coordinates(JSONWizard):
    x: int
    y: int


@dataclass
class Route(JSONWizard):
    map_id: str
    moves: list[Coordinates]
    stack_of_bags: list[Bag]


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
    snowAreas: list[SnowArea]
    children: list[Coordinates]
