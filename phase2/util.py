from requests import post, get

from constants import SUBMISSION_URL, AUTH_HEADER, MAP_URL, MAP_FILE_PATH
from data import Order, OrderResponse, Map


def send_solution(solution: Order) -> OrderResponse:
    data = solution.to_dict()
    response = post(SUBMISSION_URL, json=data, headers=AUTH_HEADER)
    return OrderResponse.from_json(response.text)


def get_map() -> Map:
    return Map.from_json(get(MAP_URL, headers=AUTH_HEADER).text)


def save(instance, path: str) -> None:
    with open(path, "w") as map_file:
        map_file.write(instance.to_json())


def load(cls, path: str):
    with open(path, "r") as map_file:
        return cls.from_json(map_file.read())


def save_map(parsed_map: Map) -> None:
    save(parsed_map, MAP_FILE_PATH)


def load_map() -> Map:
    return load(Map, MAP_FILE_PATH)