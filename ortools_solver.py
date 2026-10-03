from ortools.constraint_solver import pywrapcp, routing_enums_pb2

SCALE = 100


def solve_ortools(inst, time_limit):
    """Solveur de référence : OR-Tools Routing + Guided Local Search, même budget de temps que l'ALNS."""
    n_nodes = inst.n + 1
    manager = pywrapcp.RoutingIndexManager(n_nodes, inst.n, 0)
    routing = pywrapcp.RoutingModel(manager)
    dist = (inst.dist * SCALE).round().astype(int)
    service = (inst.service * SCALE).round().astype(int)

    def distance(i, j):
        return int(dist[manager.IndexToNode(i), manager.IndexToNode(j)])

    def travel_time(i, j):
        a, b = manager.IndexToNode(i), manager.IndexToNode(j)
        return int(service[a] + dist[a, b])

    def demand(i):
        return int(inst.demand[manager.IndexToNode(i)])

    routing.SetArcCostEvaluatorOfAllVehicles(routing.RegisterTransitCallback(distance))
    routing.AddDimensionWithVehicleCapacity(
        routing.RegisterUnaryTransitCallback(demand), 0, [inst.capacity] * inst.n, True, "Load")

    horizon = int(inst.due[0] * SCALE)
    routing.AddDimension(routing.RegisterTransitCallback(travel_time), horizon, horizon, False, "Time")
    time_dim = routing.GetDimensionOrDie("Time")
    for v in range(1, n_nodes):
        # bornes arrondies vers l'intérieur pour rester faisable en distances réelles
        time_dim.CumulVar(manager.NodeToIndex(v)).SetRange(
            int(inst.ready[v] * SCALE) + 1, int(inst.due[v] * SCALE) - 1)

    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    params.time_limit.FromMilliseconds(int(time_limit * 1000))

    sol = routing.SolveWithParameters(params)
    routes = []
    for k in range(inst.n):
        idx = routing.Start(k)
        route = []
        while not routing.IsEnd(idx):
            node = manager.IndexToNode(idx)
            if node:
                route.append(node)
            idx = sol.Value(routing.NextVar(idx))
        if route:
            routes.append(route)
    return routes
