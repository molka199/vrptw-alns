def start_times(inst, route):
    """Dates de début de service le long d'une tournée, ou None si une fenêtre est violée."""
    t, prev, times = 0.0, 0, []
    for v in route:
        t = max(t + inst.service[prev] + inst.dist[prev, v], inst.ready[v])
        if t > inst.due[v]:
            return None
        times.append(t)
        prev = v
    if t + inst.service[prev] + inst.dist[prev, 0] > inst.due[0]:
        return None
    return times


def route_load(inst, route):
    return int(sum(inst.demand[v] for v in route))


def route_cost(inst, route):
    path = [0] + route + [0]
    return float(sum(inst.dist[a, b] for a, b in zip(path, path[1:])))


def total_cost(inst, routes):
    return sum(route_cost(inst, r) for r in routes)


def check(inst, routes):
    """Vérifie : chaque client servi une fois, capacité, fenêtres de temps."""
    served = sorted(v for r in routes for v in r)
    assert served == list(range(1, inst.n + 1)), "clients manquants ou dupliqués"
    for r in routes:
        assert route_load(inst, r) <= inst.capacity, f"capacité dépassée : {r}"
        assert start_times(inst, r) is not None, f"fenêtre violée : {r}"
    return True


def can_insert(inst, route, times, p, c):
    """Teste l'insertion de c avant la position p, en propageant le décalage
    jusqu'à ce que les dates redeviennent identiques."""
    prev = route[p - 1] if p > 0 else 0
    t = times[p - 1] if p > 0 else 0.0
    t = max(t + inst.service[prev] + inst.dist[prev, c], inst.ready[c])
    if t > inst.due[c]:
        return False
    prev = c
    for k in range(p, len(route)):
        v = route[k]
        t = max(t + inst.service[prev] + inst.dist[prev, v], inst.ready[v])
        if t > inst.due[v]:
            return False
        if t == times[k]:
            return True
        prev = v
    return t + inst.service[prev] + inst.dist[prev, 0] <= inst.due[0]


def best_insertion(inst, route, times, load, c):
    """Meilleure position (surcoût, position) pour c dans la tournée, ou None."""
    if load + inst.demand[c] > inst.capacity:
        return None
    d = inst.dist
    path = [0] + route + [0]
    best = None
    for p in range(len(route) + 1):
        a, b = path[p], path[p + 1]
        delta = d[a, c] + d[c, b] - d[a, b]
        if (best is None or delta < best[0]) and can_insert(inst, route, times, p, c):
            best = (delta, p)
    return best
