from dataclasses import dataclass
from enum import Enum

from dataclass_wizard import JSONWizard, json_field


@dataclass
class Map(JSONWizard):
    pass  # TODO


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
