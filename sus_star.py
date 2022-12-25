import json
import os.path

from astar import AStar
from tqdm import tqdm

from data import Coordinates, Matrix, Circle, Route
from util import load_map, load_bags, save, cleanup_jumps_to_start, load
from checker import segment_dist, segment_time, emulate
from constants import BASE_SPEED
from itertools import product


class SusStar(AStar):

    def __init__(self, goal: Coordinates, step=50):
        self.__goal = goal
        self.step = step

    def distance_between(self, n1: Coordinates, n2: Coordinates) -> float:
        d, s, _ = segment_dist(n1, n2, map_data.snow_areas)
        return segment_time(d, s)

    def neighbors(self, node: Coordinates):
        return [self.__goal] + [node + Coordinates(*c)
                                for c in product((-self.step, 0, self.step), repeat=2) if
                                c != (0, 0) and 0 <= c[0] <= 10_000 and 0 <= c[1] <= 10_000]

    def heuristic_cost_estimate(self, current: Coordinates, goal: Coordinates) -> float:
        return current.dist(goal) / BASE_SPEED


def expand_moves(m: list[Coordinates]) -> list[Coordinates]:
    def in_c(s):
        c = Circle.from_snow(s)
        return prev_pos.in_circle(c) or next_pos.in_circle(c)

    result: list[Coordinates] = []
    prev_pos = m[0]
    for next_pos in tqdm(m[1:]):
        path = list(SusStar(next_pos,
                            10 if any(in_c(s)
                                      for s in map_data.snow_areas) else 100)
                    .astar(prev_pos, next_pos))
        result.extend(path)
        prev_pos = next_pos

    return result


if __name__ == '__main__':
    map_data = load_map()
    solution: Route = load(Route, "./data/solution_vrp.json")
    bags = load_bags()
    solution.moves = cleanup_jumps_to_start(expand_moves(solution.moves))
    print(emulate(solution, map_data))
    save(solution, "./data/solution_vrp_star.json")
