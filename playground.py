from util import (
    get_map,
    edit_json_file,
    send_solution,
    get_solution_info,
    save_map,
    load_map,
    save,
    load_bags,
)
from data import Route, Coordinates, Line, Circle
from constants import MAP_ID, MAP_FILE_PATH, IDS_FILE
import os
from checker import emulate
import visualizer
from tqdm import tqdm
from random import uniform, gauss
from simanneal import Annealer

import warnings

warnings.filterwarnings("ignore")

if __name__ == "__main__":
    if not os.path.exists(MAP_FILE_PATH):
        sus_map = get_map()
        save_map(sus_map)
    else:
        sus_map = load_map()

    circles = [Circle.from_snow(s) for s in sus_map.snow_areas]

    def penalty(f: Coordinates, t: Coordinates) -> float:
        l = Line.from_two_points(f, t)
        return sum(l.distance_in_circle(s) for s in circles)

    def optimal_path_from_base_to(f: Coordinates) -> list[Coordinates]:
        segmentation = 2

        l = f.dist(base)
        cos_a = f.x / l
        sin_a = f.y / l

        def translate(pos: Coordinates) -> Coordinates:
            return Coordinates(
                pos.x * cos_a - pos.y * sin_a,
                pos.x * sin_a + pos.y * cos_a,
            )

        def retranslate(pos: Coordinates) -> Coordinates:
            return Coordinates(
                pos.x * cos_a + pos.y * sin_a,
                pos.y * cos_a - pos.x * sin_a,
            )

        def objective(path):
            nonlocal f
            res = 0
            prev = f
            for pos in path:
                res += prev.dist(pos) + 6 * penalty(pos, prev)
                prev = pos
            res += prev.dist(base) + 6 * penalty(base, prev)
            return res * 0.001

        def mutate(path):
            nonlocal f
            mutant = [0] * len(path)
            for i, pos in enumerate(path):
                p = retranslate(pos)
                y_max = min(p.x * cos_a / sin_a, (10000 - p.x * sin_a) / cos_a)
                y_min = max(-p.x * sin_a / cos_a, (-10000 + p.x * cos_a) / sin_a)
                p.y = gauss(p.y, 300)
                p.y = max(y_min, min(y_max, p.y))
                mutant[i] = translate(p)
            return mutant

        def rand_path():
            nonlocal f
            res = [None] * segmentation
            for i in range(segmentation):
                x = l * (i + 1) / (segmentation + 1)
                y_max = min(x * cos_a / sin_a, (10000 - x * sin_a) / cos_a)
                y_min = max(-x * sin_a / cos_a, (-10000 + x * cos_a) / sin_a)
                y = uniform(y_min, y_max)
                res[i] = translate(Coordinates(x, y))
            return res

        class PathAnnealer(Annealer):
            def move(self):
                self.state = mutate(self.state)

            def energy(self):
                return objective(self.state)

        annealer = PathAnnealer(rand_path())
        accurate = {"tmax": 100.0, "tmin": 0.0087, "steps": 320, "updates": 0}
        fast = {"tmax": 100.0, "tmin": 1, "steps": 200, "updates": 0}
        annealer.set_schedule(fast)
        return [Coordinates(int(c.x), int(c.y)) for c in annealer.anneal()[0]]

    stack_of_bags = load_bags()

    moves = []
    base = Coordinates(0, 0)
    curr_pos = Coordinates(0, 0)

    def update_curr_pos(value):
        global curr_pos
        moves.append(value)
        curr_pos = value

    unvisited = set(child_pos for child_pos in sus_map.children)
    for bag in tqdm(
        list(reversed(stack_of_bags))
    ):  # since it's a stack, the order is reversed
        for i, _ in enumerate(bag):
            nearest_child_pos = None
            metric = 10**100
            for child_pos in unvisited:
                m = child_pos.dist(curr_pos)
                if m >= metric:
                    continue
                # m = out_circ + 7*in_circ = (m - in_circ) + 7 * in_circ
                m += 6 * penalty(child_pos, curr_pos)
                if nearest_child_pos is None or m < metric:
                    nearest_child_pos = child_pos
                    metric = m
            if i == 0:
                # go to the first child using segmented path
                moves.extend(optimal_path_from_base_to(nearest_child_pos))
                curr_pos = nearest_child_pos
            update_curr_pos(nearest_child_pos)
            unvisited.remove(nearest_child_pos)

        # go back using segmented path
        moves.extend(reversed(optimal_path_from_base_to(curr_pos)))
        curr_pos = base

    sus_solution = Route(moves=moves, map_id=MAP_ID, stack_of_bags=stack_of_bags)
    print("=== SOLUTION ===")
    print(sus_solution)
    visualizer.visualize_route(sus_map, sus_solution).save("data/route.png")
    print(emulate(sus_solution, sus_map))
    if input("Send solution? y/n: ").lower() in ("y", "yes"):
        sus_response = send_solution(sus_solution)
        print("=== RESPONSE ===")
        print(sus_response)
        print("=== INFO ===")
        if sus_response.success:
            print(get_solution_info(sus_response.round_id))
            with edit_json_file(IDS_FILE) as solution:
                solution[sus_response.round_id] = input("label: ")
            save(sus_solution, f"./data/solution_{sus_response.round_id}.json")
        else:
            print("Unsuccessful")
            save(sus_solution, "./data/solution_unsuccessful.json")
