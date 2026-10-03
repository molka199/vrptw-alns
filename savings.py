from .solution import route_load, start_times


def clarke_wright(inst):
    """Heuristique des économies (Clarke & Wright, 1964) avec fenêtres de temps.
    Fusionne r1 + r2 quand i termine r1, j commence r2 et que la tournée fusionnée reste faisable."""
    d = inst.dist
    routes = {i: [i] for i in range(1, inst.n + 1)}
    owner = {i: i for i in range(1, inst.n + 1)}

    savings = sorted(
        ((d[0, i] + d[0, j] - d[i, j], i, j)
         for i in range(1, inst.n + 1) for j in range(1, inst.n + 1) if i != j),
        reverse=True,
    )
    for s, i, j in savings:
        if s <= 0:
            break
        ri, rj = owner[i], owner[j]
        if ri == rj or routes[ri][-1] != i or routes[rj][0] != j:
            continue
        merged = routes[ri] + routes[rj]
        if route_load(inst, merged) > inst.capacity or start_times(inst, merged) is None:
            continue
        routes[ri] = merged
        for v in routes.pop(rj):
            owner[v] = ri

    return list(routes.values())
