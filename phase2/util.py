import json
from collections import defaultdict

from requests import post, get

from constants import SUBMISSION_URL, AUTH_HEADER, MAP_URL, MAP_FILE_PATH, INFO_URL_TEMPLATE
from data import Order, OrderResponse, Map, RoundInfo


class edit_json_file:
    def __init__(self, path, default={}):
        self.path = path
        self.default = default

    def __enter__(self):
        try:
            with open(self.path, "r") as tmp:
                self.res = json.load(tmp)
        except:
            self.res = self.default
        self.file = open(self.path, "a+")
        return self.res

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.file.truncate(0)
        json.dump(self.res, self.file)
        self.file.close()


class read_json_file:
    def __init__(self, path, default={}):
        self.path = path
        self.default = default

    def __enter__(self):
        try:
            tmp = open(self.path, "r")
            self.res = json.load(tmp)
            tmp.close()
        except:
            self.res = self.default
        return self.res

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


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


def get_solution_info(solution_id: str) -> RoundInfo:
    response = get(INFO_URL_TEMPLATE % solution_id, headers=AUTH_HEADER)
    return RoundInfo.from_json(response.text)


def info_about_map(m: Map) -> None:
    print("=== MAP INFO ===")
    print(f"Number of children: {len(m.children)}")
    genders = {c.gender for c in m.children}
    print(f"Genders: {genders}")
    ages = {c.age for c in m.children}
    print(f"Ages: {ages}")

    age_to_child = defaultdict(int)
    for c in m.children:
        age_to_child[c.age] += 1
    print(f"Age to child: {list(sorted(age_to_child.items()))}")

    gender_to_child = defaultdict(int)
    for c in m.children:
        gender_to_child[c.gender] += 1
    print(f"Gender to child: {list(sorted(gender_to_child.items()))}")

    print(f"Number of gifts: {len(m.gifts)}")
    prices = {g.price for g in m.gifts}
    print("Min and max price of gifts: ", min(prices), max(prices))
    types = {g.type for g in m.gifts}
    print(f"Types: {types}")

    children_ids = {c.id for c in m.children}
    assert children_ids == set(range(1, len(m.children) + 1))
    gift_ids = {g.id for g in m.gifts}
    assert gift_ids == set(range(1, len(m.gifts) + 1))
    print(f"Ids for gifts and childrens are {range(1, len(m.children) + 1)}")
