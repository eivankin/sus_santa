import json
from constants import (
    SUBMISSION_URL,
    AUTH_HEADER,
    MAP_URL,
    INFO_URL_TEMPLATE,
    MAP_FILE_PATH, SNOW_SPEED, BASE_SPEED,
)
from data import Route, RouteResponse, RoundInfo, Map, Bag, Coordinates, SnowArea, Line, Circle
from requests import post, get


class edit_json_file:
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
        self.file = open(self.path, "w")
        return self.res

    def __exit__(self, exc_type, exc_val, exc_tb):
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


def send_solution(solution: Route) -> RouteResponse:
    data = solution.to_dict()
    response = post(SUBMISSION_URL, json=data, headers=AUTH_HEADER)
    return RouteResponse.from_json(response.text)


def get_map() -> Map:
    return Map.from_json(get(MAP_URL, headers=AUTH_HEADER).text)


def get_solution_info(solution_id: str) -> RoundInfo:
    response = get(INFO_URL_TEMPLATE % solution_id, headers=AUTH_HEADER)
    return RoundInfo.from_json(response.text)


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


def info_about_map(m: Map) -> None:
    print("=== MAP INFO ===")
    min_x, min_y, max_x, max_y = 1e10, 1e10, 0, 0
    for child in m.children:
        min_x = min(min_x, child.x)
        min_y = min(min_y, child.y)
        max_x = max(max_x, child.x)
        max_y = max(max_y, child.y)
    print("Children coords info")
    print(f"{min_x=}, {min_y=}, {max_x=}, {max_y=}")
    print(f"Number of children: {len(m.children)}")
    print(f"Number of gifts: {len(m.gifts)}")
    print(f"Number of snow areas: {len(m.snow_areas)}")


def load_bags() -> list[Bag]:
    stack_of_bags = []
    with open("data/bin_packing_result_best.json", "r") as f:
        for bag in json.load(f):
            stack_of_bags.append(bag["gift_ids"])
    return stack_of_bags


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


def st(n1: Coordinates, n2: Coordinates, snow_areas: list[SnowArea]):
    d, s, _ = segment_dist(n1, n2, snow_areas)
    return segment_time(d, s)


def path_len(moves: list[Coordinates], snow_areas: list[SnowArea]):
    return sum(st(a, b, snow_areas) for a, b in zip(moves[:-1], moves[1:]))


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


def segment_time(dist: float, snow_dist: float) -> float:
    return snow_dist / SNOW_SPEED + (dist - snow_dist) / BASE_SPEED
