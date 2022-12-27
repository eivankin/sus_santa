import os
import warnings

from constants import MAP_FILE_PATH, MAP_ID, IDS_FILE, SOLUTIONS_PATH
from phase2.data import Order, Present, Map
from util import (
    get_map,
    save_map,
    load_map,
    info_about_map,
    send_solution,
    get_solution_info,
    edit_json_file,
    save,
    load,
)
from greedy import (
    most_expensive,
    pass_weights,
    get_best_fit_with_weights,
    calc_values_for_knapsack,
    get_sol_cost,
)
from happiness_estimator import eval_solution, Weights, WEIGHTS_PATH, load_all_solutions
from checker import validate

if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    if not os.path.exists(MAP_FILE_PATH):
        sus_map: Map = get_map()
        save_map(sus_map)
    else:
        sus_map: Map = load_map()

    info_about_map(sus_map)

    weights = load(Weights, WEIGHTS_PATH)
    solutions = load_all_solutions()
    best = max(solutions.values(), key=lambda x: x[1])
    print(
        f"Best score so far: actual={best[1]}, "
        f"calculated={eval_solution(best[0], sus_map, weights)}"
    )

    id_to_gift = {g.id: g for g in sus_map.gifts}
    gifts = [id_to_gift[gid] for gid in sorted(id_to_gift)]
    presents = most_expensive(
        gifts,
        sus_map.children.copy(),
        fit_function=pass_weights(weights, get_best_fit_with_weights),
        use_knapsack=True,
        knapsack_value_function=pass_weights(weights, calc_values_for_knapsack),
        shuffle_children=True,
    )
    sus_solution = Order(MAP_ID, presents)
    validate(sus_solution, sus_map)
    print(f"Score: {eval_solution(sus_solution, sus_map, weights)}")
    print("Cost:", get_sol_cost(sus_map, sus_solution))

    if input("Send solution? y/n: ").lower() in ("y", "yes"):
        sus_response = send_solution(sus_solution)
        print(sus_response)
        if sus_response.success:
            print(get_solution_info(sus_response.round_id))
            with edit_json_file(IDS_FILE) as solution:
                solution[sus_response.round_id] = input("label: ")
            save(sus_solution, SOLUTIONS_PATH + f"{sus_response.round_id}.json")
        else:
            print("Unsuccessful")
            save(sus_solution, "./data/solution_unsuccessful.json")
