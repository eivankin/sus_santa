import json
from collections import defaultdict

from requests import post, get

from constants import (
    SUBMISSION_URL,
    AUTH_HEADER,
    MAP_URL,
    MAP_FILE_PATH,
    INFO_URL_TEMPLATE,
)
from constants import BASE_SPEED, WIND_SPEED, SNOW_SPEED
from data import (
    Solution,
    SolutionResponse,
    Map,
    RoundInfo,
    Coordinates,
    SnowArea,
    Line,
    Circle,
    Bag,
)


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


def send_solution(solution: Solution) -> SolutionResponse:
    data = solution.to_dict()
    response = post(SUBMISSION_URL, json=data, headers=AUTH_HEADER)
    return SolutionResponse.from_json(response.text)


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
    print("Avg price: ", sum(prices) / len(prices))
    types = {g.type for g in m.gifts}
    print(f"Types: {types}")

    # children_ids = {c.id for c in m.children}
    # assert children_ids == set(range(1, len(m.children) + 1))
    gift_ids = {g.id for g in m.gifts}
    assert gift_ids == set(range(1, len(m.gifts) + 1))
    print(f"Ids for gifts and childrens are {range(1, len(m.children) + 1)}")
    min_x, min_y, max_x, max_y = 1e10, 1e10, 0, 0
    for child in m.children:
        min_x = min(min_x, child.x)
        min_y = min(min_y, child.y)
        max_x = max(max_x, child.x)
        max_y = max(max_y, child.y)
    print("Children coords info")
    print(f"{min_x=}, {min_y=}, {max_x=}, {max_y=}")
    print(f"Number of snow areas: {len(m.snow_areas)}")


def cleanup_jumps_to_start(old_moves: list[Coordinates]):
    moves = [Coordinates(0, 0)]
    for c in old_moves:
        if c != moves[-1]:
            moves.append(c)

    moves.pop(0)

    if moves[-1] == Coordinates(0, 0):
        moves.pop()
    if moves[0] == Coordinates(0, 0):
        moves.pop(0)
    return moves


def load_bags() -> list[Bag]:
    stack_of_bags = []
    with open("data/bin_packing_result_best.json", "r") as f:
        for bag in json.load(f):
            stack_of_bags.append(bag["gift_ids"])
    return stack_of_bags


def segment_dist(
    from_pos: Coordinates, to_pos: Coordinates, snow_areas: list[SnowArea]
) -> tuple[float, float, list[float]]:
    dist = from_pos.dist(to_pos)
    line = Line.from_two_points(from_pos, to_pos)
    distances_in_snow = [
        line.distance_in_circle(Circle.from_snow(snow)) for snow in snow_areas
    ]
    snow_dist = sum(distances_in_snow)
    assert snow_dist <= dist or snow_dist - dist < 1
    return dist, snow_dist, distances_in_snow


def segment_time(dist: float, snow_dist: float, direction: Coordinates = None) -> float:
    if direction is not None:
        # strange wind proportion
        k = direction.x / (abs(direction.x) + abs(direction.y))
        speed = BASE_SPEED + WIND_SPEED * k
    else:
        speed = BASE_SPEED
    return snow_dist / SNOW_SPEED + (dist - snow_dist) / speed
