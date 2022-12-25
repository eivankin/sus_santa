import json
import os.path

from astar import find_path
from tqdm import tqdm

from constants import MAP_ID
from data import Coordinates, Matrix, Circle, Route
from util import load_map, load_bags, save, cleanup_jumps_to_start
from vrp import solve

FILE_PATH = './data/matrix_best.json'


def shortest_path(
        from_pos: int, to_pos: int, times: Matrix, vertices: list[Coordinates],
        num_children
) -> tuple[float, list[int]]:
    def get_neighbors(node: int):
        return [to_pos] + [n for n in range(num_children + 1, len(vertices)) if n != node]

    def distance(n1: int, n2: int):
        return times[n1][n2]

    def heuristic(current: int, goal: int):
        return 0

    path = list(find_path(
        from_pos,
        to_pos,
        get_neighbors,
        heuristic_cost_estimate_fnct=heuristic,
        distance_between_fnct=distance
    ))
    path_len = sum(times[f][t] for f, t in zip(path[:-1], path[1:]))
    return path_len, path


def expand_moves(m: list[Coordinates], table: dict[str, list[int]],
                 vertices: list[Coordinates]) -> list[Coordinates]:
    coords_to_id = {coords: idx for idx, coords in enumerate(vertices)}
    result: list[Coordinates] = []
    prev_pos = m[0]
    for next_pos in m[1:]:
        from_idx = coords_to_id[prev_pos]
        to_idx = coords_to_id[next_pos]
        if from_idx > to_idx:
            key = f'{from_idx}-{to_idx}'
        else:
            key = f'{to_idx}-{from_idx}'

        result.extend([v[n] for n in table.get(key, [from_idx, to_idx])])
        prev_pos = next_pos

    return result


if __name__ == '__main__':
    map_data = load_map()
    v = [Coordinates(0, 0)] + map_data.children + \
        sum((Circle.from_snow(s).get_outer_points() for s in map_data.snow_areas), [])

    if not os.path.exists(FILE_PATH):
        with open("./data/matrix.json", "r") as inp:
            matrix = json.load(inp)

        n_children = len(map_data.children)

        best_times: Matrix = [[0] * (n_children + 1) for _ in range(n_children + 1)]
        edges_to_paths: dict[str, list[int]] = {}
        with tqdm(total=(n_children + 1) ** 2 // 2) as pbar:
            for i in range((n_children + 1)):
                for j in range((n_children + 1)):
                    if i > j:
                        bl, p = shortest_path(i, j, matrix, v, n_children)
                        best_times[i][j] = best_times[j][i] = bl
                        edges_to_paths[f'{i}-{j}'] = p
                        pbar.update()

        with open(FILE_PATH, 'w') as out:
            json.dump({'matrix': best_times, 'edges': edges_to_paths}, out)
    else:
        with open(FILE_PATH, 'r') as inp:
            saved = json.load(inp)

        best_times = saved['matrix']
        edges_to_paths = saved['edges']
    bags = load_bags()
    moves = solve(map_data, bags, best_times)
    expanded = cleanup_jumps_to_start(expand_moves(moves, edges_to_paths, v))
    solution = Route(moves=expanded, stack_of_bags=bags, map_id=MAP_ID)
    save(solution, "./data/solution_vrp_star.json")
