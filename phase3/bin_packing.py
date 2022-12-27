from __future__ import annotations

import json
import os.path
import pickle

from ortools.linear_solver import pywraplp

from phase3.data import Map, Gift
from util import load_map


def create_data_model(gifts: list[Gift]) -> dict:
    """Create the data for the example."""
    data = {}

    weights, volumes, ids = [], [], []
    print("Number of gifts:", len(gifts))
    for i, gift in enumerate(gifts):
        weights.append(gift.weight)
        volumes.append(gift.volume)
        ids.append(gift.id)

    # assert ids == list(range(1, len(ids) + 1))

    data["weights"] = weights
    data["volumes"] = volumes
    data["items"] = list(range(len(weights)))
    data["bins"] = list(range(46))
    data["max_weight"] = 200
    data["max_volume"] = 100
    data["ids"] = ids
    return data


def solve_bin_pack(gifts: list[Gift], time_limit=3000) -> list[dict] | None:
    if os.path.exists('./data/bin_packing_result.json'):
        with open('./data/bin_packing_result.json', 'r') as inp:
            return json.load(inp)
    data = create_data_model(gifts)

    # Create the mip solver with the SCIP backend.
    solver = pywraplp.Solver.CreateSolver("SCIP")
    solver.set_time_limit(time_limit)

    if not solver:
        return

    solver.EnableOutput()

    # Variables
    # x[i, j] = 1 if item i is packed in bin j.

    x = {}
    for i in data["items"]:
        for j in data["bins"]:
            x[(i, j)] = solver.IntVar(0, 1, "x_%i_%i" % (i, j))

    # y[j] = 1 if bin j is used.
    y = {}
    for j in data["bins"]:
        y[j] = solver.IntVar(0, 1, "y[%i]" % j)

    # Constraints
    # Each item must be in exactly one bin.
    for i in data["items"]:
        solver.Add(sum(x[i, j] for j in data["bins"]) == 1)

    print("Computing constraints on weight and volume...")
    # The amount packed in each bin cannot exceed its max weight and max volume.
    for j in data["bins"]:
        solver.Add(
            sum(x[(i, j)] * data["weights"][i] for i in data["items"])
            <= y[j] * data["max_weight"]
        )
        solver.Add(
            sum(x[(i, j)] * data["volumes"][i] for i in data["items"])
            <= y[j] * data["max_volume"]
        )

    # Objective: minimize the number of bins used.

    # solver.Minimize(solver.Sum([y[j] for j in data['bins']]))
    # solver.Minimize(sum([x[(i, 45)] for i in data["items"]]))

    # for

    status = solver.Solve()

    if status == pywraplp.Solver.OPTIMAL:
        num_bins = 0
        res = []
        for j in data["bins"]:
            if y[j].solution_value() == 1:
                bin_items = []
                bin_weight = 0
                bin_volume = 0
                for i in data["items"]:
                    if x[i, j].solution_value() > 0:
                        bin_items.append(i)
                        bin_weight += data["weights"][i]
                        bin_volume += data["volumes"][i]
                if bin_items:
                    num_bins += 1
                    ids = [data["ids"][i] for i in bin_items]
                    print("Bin number", j)
                    print("  Items packed:", ids)
                    print("  Total weight:", bin_weight)
                    print("  Total volume:", bin_volume)
                    print()
                    bin_res = {
                        "weight": bin_weight,
                        "volume": bin_volume,
                        "gift_ids": ids,
                    }
                    res.append(bin_res)
                    with open("bin_packing_result.json", "w") as f:
                        f.write(json.dumps(res))
        # with open("bin_packing_result.json", "w") as f: # mb down here?
        #                 f.write(json.dumps(res))
        print()
        print("Number of bins used:", num_bins)
        print("Time = ", solver.WallTime(), " milliseconds")
        return res
    else:
        print("The problem does not have an optimal solution.")


if __name__ == "__main__":
    solve_bin_pack()
