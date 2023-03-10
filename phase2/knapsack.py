from ortools.algorithms import pywrapknapsack_solver


def solve(
    values: list[int], weights: list[list[int]], capacities: list[int]
) -> list[int]:
    # Create the solver.
    solver = pywrapknapsack_solver.KnapsackSolver(
        pywrapknapsack_solver.KnapsackSolver.KNAPSACK_MULTIDIMENSION_BRANCH_AND_BOUND_SOLVER,
        "KnapsackExample",
    )
    solver.set_time_limit(1)

    solver.Init(values, weights, capacities)
    computed_value = solver.Solve()

    packed_items = []
    packed_weights = []
    total_weight = 0
    print("Total value =", computed_value)
    for i in range(len(values)):
        if solver.BestSolutionContains(i):
            packed_items.append(i)
            packed_weights.append(weights[0][i])
            total_weight += weights[0][i]
    print("Total weight:", total_weight)
    print("Packed items:", packed_items)
    print("Packed_weights:", packed_weights)
    return packed_items
