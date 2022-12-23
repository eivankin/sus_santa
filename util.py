from constants import SUBMISSION_URL, AUTH_HEADER, MAP_URL, INFO_URL_TEMPLATE, MAP_FILE_PATH
from data import Route, RouteResponse, RoundInfo, Map
from requests import post, get


def send_solution(solution: Route) -> RouteResponse:
    data = solution.to_dict()
    response = post(SUBMISSION_URL, json=data, headers=AUTH_HEADER)
    return RouteResponse.from_json(response.text)


def get_map() -> Map:
    return Map.from_json(get(MAP_URL, headers=AUTH_HEADER).text)


def get_solution_info(solution_id: str) -> RoundInfo:
    response = get(INFO_URL_TEMPLATE % solution_id, headers=AUTH_HEADER)
    return RoundInfo.from_json(response.text)


def save_map(parsed_map: Map) -> None:
    with open(MAP_FILE_PATH, 'w') as map_file:
        map_file.write(parsed_map.to_json())


def load_map() -> Map:
    with open(MAP_FILE_PATH, 'r') as map_file:
        return Map.from_json(map_file.read())


def info_about_map(m: Map) -> None:
    print('=== MAP INFO ===')
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
