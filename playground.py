from util import get_map, send_solution, get_solution_info, save_map, load_map, save
from data import Route, Coordinates, Line, Circle
from constants import MAP_ID, MAP_FILE_PATH, IDS_FILE
import os
from checker import emulate
import visualizer
import json
from tqdm import tqdm
from annealer import simulated_annealing
from random import uniform
from math import pi

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

    def optimal_path_to_base(f: Coordinates) -> list[Coordinates]:
        # path = [(a0, r0), (), (), (), ()]  # starting from f, ending with t, r0 > r1 > r2 ..

        def objective(path):
            nonlocal f
            res = 0
            prev = f
            for (a, r) in path:
                pos = Coordinates.from_polar(r, a)
                res += prev.dist(pos) + 6 * penalty(pos, prev)
                prev = pos
            res += prev.dist(base)
            return res * 0.001

        def mutate(path):
            return rand_path()

        def rand_path():
            nonlocal f
            res = [None] * 5
            r = f.dist(base)
            for i in range(5):
                r = uniform(10, r)
                res[i] = (uniform(0, pi / 2), r)
            return res

        return [
            Coordinates.from_polar(a, r)
            for (a, r) in simulated_annealing(rand_path(), objective, mutate)
        ]

    stack_of_bags = []
    with open("data/bin_packing_result.json", "r") as f:
        for bag in json.load(f):
            stack_of_bags.append(bag["gift_ids"])

    moves = []
    base = Coordinates(0, 0)
    curr_pos = Coordinates(0, 0)

    def update_curr_pos(value):
        global curr_pos
        moves.append(value)
        curr_pos = value

    unvisited = set(child_pos for child_pos in sus_map.children)
    with tqdm(total=sum(len(bag) for bag in stack_of_bags)) as pbar:
        for bag in reversed(stack_of_bags):  # since it's a stack, the order is reversed
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
                    for pos in reversed(optimal_path_to_base(nearest_child_pos)):
                        update_curr_pos(pos)
                    update_curr_pos(nearest_child_pos)
                else:
                    update_curr_pos(nearest_child_pos)
                unvisited.remove(nearest_child_pos)
                pbar.update(1)

            # go back using segmented path
            for pos in optimal_path_to_base(curr_pos):
                update_curr_pos(pos)
            update_curr_pos(base)

    sus_solution = Route(moves=moves, map_id=MAP_ID, stack_of_bags=stack_of_bags)
    print("=== SOLUTION ===")
    print(sus_solution)
    visualizer.visualize_route(sus_map, sus_solution).save("data/route.png")
    print(emulate(sus_solution, sus_map))
    if input('Save solution? y/n: ').lower() in ('y', 'yes'):
        sus_response = send_solution(sus_solution)
        print("=== RESPONSE ===")
        print(sus_response)
        print("=== INFO ===")
        if sus_response.success:
            print(get_solution_info(sus_response.round_id))
            content = None
            try:
                with open(IDS_FILE, "r") as solution_file:
                    content = json.load(solution_file)
            except:
                content = {}
            with open(IDS_FILE, "w") as solution_file:
                content[sus_response.round_id] = input()
                json.dump(content, solution_file)
            save(sus_solution, f'./data/solution_{sus_response.round_id}.json')
        else:
            print("Unsuccessful")

