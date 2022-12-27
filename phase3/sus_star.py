from __future__ import annotations

import json
import os.path
from collections import defaultdict
from math import ceil, sqrt

from astar import AStar
from tqdm import tqdm

from data import Coordinates, Matrix, Circle, Route
# from optimal_path import PenatyChecker, ObjectiveChecker, WidePathMutator
from util import load_map, load_bags, save, cleanup_jumps_to_start, load, path_len
from checker import segment_dist, segment_time, emulate
from constants import BASE_SPEED, MAX_COORD
from itertools import product
from functools import lru_cache
# from optimal_path import OptimalPathFinder

BASE_STEP = 100
CACHE_SIZE = 65536 * 2


@lru_cache(maxsize=CACHE_SIZE)
def is_near_circle(node: Coordinates, buff=BASE_STEP) -> bool:
    for s in map_data.snow_areas:
        c = Circle.from_snow(s)
        c.radius += buff
        if node.in_circle(c):
            return True
    return False


@lru_cache(maxsize=CACHE_SIZE)
def get_outside(node: Coordinates) -> Coordinates | None:
    for s in map_data.snow_areas:
        c = Circle.from_snow(s)
        if node.in_circle(c):
            return get_nearest_point_outside(c, node)
    return None


class SusStar(AStar):
    def __init__(self, goal: Coordinates, step: int = None):
        self.__goal = goal
        self.__goal_outside = get_outside(goal)
        self.step = step

    def distance_between(self, n1: Coordinates, n2: Coordinates) -> float:
        d, s, _ = segment_dist(n1, n2, map_data.snow_areas)
        return segment_time(d, s)

    def neighbors(self, node: Coordinates) -> list[Coordinates]:
        result = [self.__goal] + outer
        node_outside = get_outside(node)
        if node_outside:
            result.append(node_outside)
        if self.__goal_outside:
            result.append(self.__goal_outside)

        if self.step is not None:
            step = self.step
            result.extend(
                [
                    node + Coordinates(*c)
                    for c in product((-step, 0, step), repeat=2)
                    if c != (0, 0) and 0 <= c[0] <= 10_000 and 0 <= c[1] <= 10_000
                ]
            )

        return result

    def heuristic_cost_estimate(self, current: Coordinates, goal: Coordinates) -> float:
        return current.dist(goal) / BASE_SPEED


def expand_moves(m: list[Coordinates]) -> list[Coordinates]:
    result: list[Coordinates] = []
    prev_pos = m[0]
    for next_pos in tqdm(m[1:]):
        prev_out = get_outside(prev_pos) or prev_pos
        next_out = get_outside(next_pos) or next_pos
        path = min(
            [prev_pos, next_pos],
            [prev_pos, prev_out, next_out, next_pos],
            # optimal_path(prev_pos, next_pos),
            # [prev_pos] + optimal_path(prev_out, next_out) + [next_pos],
            list(SusStar(next_pos).astar(prev_pos, next_pos)),
            key=pl,
        )
        result.extend(path)
        prev_pos = next_pos

    return result


def pl(p):
    return path_len(p, map_data.snow_areas)


# @lru_cache(maxsize=CACHE_SIZE)
# def optimal_path(start: Coordinates, end: Coordinates):
#     return (
#         OptimalPathFinder(
#             max(2, int(start.dist(end) / 2_000)),
#             WidePathMutator(1, 3000, 3000).mutate,
#             ObjectiveChecker(penalty).objective,
#             schedule={"tmax": 100, "tmin": 1, "steps": 1_000, "updates": 0},
#         )
#         .optimal_path(start, end)
#         .path
#     )


def clamp(val, lower, upper):
    if val < lower:
        return lower
    if val > upper:
        return upper
    return val


def get_nearest_point_outside(circle: Circle, inside_pos: Coordinates):
    diff = inside_pos - circle.center
    diff = diff * (circle.radius / diff.dist(Coordinates(0, 0)))
    diff.x = ceil(diff.x)
    diff.y = ceil(diff.y)
    result = diff + circle.center
    if not result.in_bounds():
        if (0 <= result.x <= 10_000) != (0 <= result.y <= 10_000):
            if result.x < 0 or result.x > MAX_COORD:
                x = clamp(result.x, 0, MAX_COORD)
                y = (
                        round(
                            (-1 if inside_pos.y < circle.center.y else 1)
                            * sqrt(circle.radius ** 2 - (circle.center.x - x) ** 2)
                        )
                        - circle.center.y
                )
            else:
                y = clamp(result.y, 0, MAX_COORD)
                x = (
                        round(
                            (-1 if inside_pos.x < circle.center.x else 1)
                            * sqrt(circle.radius ** 2 - (circle.center.y - y) ** 2)
                        )
                        - circle.center.x
                )
            return Coordinates(x, y)
        else:
            return inside_pos
    return result


def make_matrix(vertices: list[Coordinates]):
    num_v = len(vertices)
    result = [[0] * num_v for _ in range(num_v)]
    edges: dict[str, dict[str, list[Coordinates]]] = defaultdict(dict)
    with tqdm(total=num_v * num_v // 2) as pbar:
        for i in range(num_v):
            for j in range(num_v):
                if i > j:
                    prev_pos = vertices[i]
                    next_pos = vertices[j]
                    prev_out = get_outside(prev_pos) or prev_pos
                    next_out = get_outside(next_pos) or next_pos
                    paths = [
                        [prev_pos, next_pos],
                        [prev_pos, prev_out, next_out, next_pos],
                        # optimal_path(prev_pos, next_pos),
                        # [prev_pos] + optimal_path(prev_out, next_out) + [next_pos],
                        list(SusStar(next_pos).astar(prev_pos, next_pos))
                    ]
                    path = max(((p, pl(p)) for p in paths), key=lambda x: x[1])
                    moves, length = path
                    result[i][j] = result[j][i] = length
                    edges[prev_pos.to_str()][next_pos.to_str()] = moves
                    pbar.update()

    with open('./data/star_matrix.json') as out:
        json.dump(result, out)

    with open('./data/star_edges.json') as out:
        json.dump(edges, out)


if __name__ == "__main__":
    map_data = load_map()
    vs: list[Coordinates] = [Coordinates(0, 0)] + map_data.children

    circles = [Circle.from_snow(s) for s in map_data.snow_areas]
    # penalty = PenatyChecker(circles).penalty
    # objective = ObjectiveChecker(penalty).objective

    outer = sum(
        (Circle.from_snow(s).get_outer_points() for s in map_data.snow_areas), []
    )

    # make_matrix(vs)
    #
    solution: Route = load(Route, "./data/solutions/01GNA6WHX38DG24628XR8ZWXS7.json")
    bags = load_bags()
    solution.moves = cleanup_jumps_to_start(expand_moves(solution.moves))
    save(solution, f"./data/star.json")
    res = emulate(solution, map_data)
    print(res)
