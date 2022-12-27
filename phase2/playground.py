import os
import warnings

from constants import MAP_FILE_PATH, MAP_ID, IDS_FILE, SOLUTIONS_PATH
from phase2.data import Order, Present
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
from greedy import most_expensive, get_fit_function
from happiness_estimator import eval_solution, Weights, WEIGHTS_PATH, load_all_solutions
from checker import validate

if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    if not os.path.exists(MAP_FILE_PATH):
        sus_map = get_map()
        save_map(sus_map)
    else:
        sus_map = load_map()

    info_about_map(sus_map)

    # presents = [Present(i, i) for i in range(1, 1001)]
    weights = load(Weights, WEIGHTS_PATH)
    solutions = load_all_solutions()
    scores = [x[1] for x in solutions.values()]
    print(f"Best score so far: {max(scores)}")

    presents = most_expensive(sus_map, get_fit_function(weights))
    # presents[0].gift_id = 2000
    sus_solution = Order(MAP_ID, presents)
    validate(sus_solution, sus_map)
    print(f"Score: {eval_solution(sus_solution, sus_map, weights)}")

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
