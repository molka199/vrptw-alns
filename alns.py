"""Adaptive Large Neighborhood Search (Ropke & Pisinger, 2006) pour le VRPTW.
Destruction : aléatoire, pire coût, proximité (Shaw).
Réparation : insertion gloutonne, insertion par regret-2.
Acceptation : recuit simulé. Poids des opérateurs adaptés par segments."""
import math
import time

import numpy as np

from .solution import best_insertion, route_cost, route_load, start_times, total_cost


class State:
    def __init__(self, inst, routes):
        self.inst = inst
        self.routes = [list(r) for r in routes if r]
        self.times = [start_times(inst, r) for r in self.routes]
        self.loads = [route_load(inst, r) for r in self.routes]

    def copy(self):
        s = State.__new__(State)
        s.inst = self.inst
        s.routes = [list(r) for r in self.routes]
        s.times = [list(t) for t in self.times]
        s.loads = list(self.loads)
        return s

    def cost(self):
        return total_cost(self.inst, self.routes)

    def refresh(self, k):
        self.times[k] = start_times(self.inst, self.routes[k])
        self.loads[k] = route_load(self.inst, self.routes[k])

    def remove(self, customers):
        removed = set(customers)
        for k, r in enumerate(self.routes):
            if removed.intersection(r):
                self.routes[k] = [v for v in r if v not in removed]
                self.refresh(k)
        keep = [k for k, r in enumerate(self.routes) if r]
        self.routes = [self.routes[k] for k in keep]
        self.times = [self.times[k] for k in keep]
        self.loads = [self.loads[k] for k in keep]


# ---------- destruction ----------

def random_removal(state, q, rng):
    customers = [v for r in state.routes for v in r]
    return list(rng.choice(customers, size=q, replace=False))


def worst_removal(state, q, rng, p=3):
    d = state.inst.dist
    gains = []
    for r in state.routes:
        path = [0] + r + [0]
        for k, v in enumerate(r):
            a, b = path[k], path[k + 2]
            gains.append((d[a, v] + d[v, b] - d[a, b], v))
    gains.sort(reverse=True)
    chosen = []
    while len(chosen) < q:
        k = int(len(gains) * rng.random() ** p)
        chosen.append(gains.pop(k)[1])
    return chosen


def shaw_removal(state, q, rng, p=6):
    inst = state.inst
    customers = [v for r in state.routes for v in r]
    dmax = inst.dist.max()
    tmax = inst.due[0]
    chosen = [int(rng.choice(customers))]
    rest = [v for v in customers if v != chosen[0]]
    while len(chosen) < q:
        ref = chosen[int(rng.integers(len(chosen)))]
        rest.sort(key=lambda v: inst.dist[ref, v] / dmax + abs(inst.ready[ref] - inst.ready[v]) / tmax)
        k = int(len(rest) * rng.random() ** p)
        chosen.append(rest.pop(k))
    return chosen


# ---------- réparation ----------

def insert(state, unassigned, regret):
    inst = state.inst
    cache = {c: [best_insertion(inst, r, t, l, c)
                 for r, t, l in zip(state.routes, state.times, state.loads)]
             for c in unassigned}
    pending = set(unassigned)

    while pending:
        pick, pick_score, pick_move = None, None, None
        for c in pending:
            opts = sorted((m[0], k, m[1]) for k, m in enumerate(cache[c]) if m is not None)
            if not opts:
                score = math.inf
                move = None
            elif regret:
                score = opts[1][0] - opts[0][0] if len(opts) > 1 else math.inf
                move = opts[0]
            else:
                score = -opts[0][0]
                move = opts[0]
            if pick is None or score > pick_score:
                pick, pick_score, pick_move = c, score, move

        pending.remove(pick)
        if pick_move is None:
            state.routes.append([pick])
            state.times.append(start_times(inst, [pick]))
            state.loads.append(int(inst.demand[pick]))
            k = len(state.routes) - 1
            for c in pending:
                cache[c].append(None)
        else:
            _, k, pos = pick_move
            state.routes[k].insert(pos, pick)
            state.refresh(k)
        r, t, l = state.routes[k], state.times[k], state.loads[k]
        for c in pending:
            cache[c][k] = best_insertion(inst, r, t, l, c)


def greedy_insert(state, unassigned):
    insert(state, unassigned, regret=False)


def regret_insert(state, unassigned):
    insert(state, unassigned, regret=True)


# ---------- boucle principale ----------

def alns(inst, initial_routes, iterations=3000, seed=0, segment=100, reaction=0.1):
    rng = np.random.default_rng(seed)
    destroy_ops = [random_removal, worst_removal, shaw_removal]
    repair_ops = [greedy_insert, regret_insert]
    w_d, w_r = np.ones(len(destroy_ops)), np.ones(len(repair_ops))
    s_d, s_r = np.zeros(len(destroy_ops)), np.zeros(len(repair_ops))
    n_d, n_r = np.zeros(len(destroy_ops)), np.zeros(len(repair_ops))

    current = State(inst, initial_routes)
    best = current.copy()
    cur_cost = best_cost = current.cost()

    # T0 : une solution 5 % plus chère est acceptée avec probabilité 0,5
    temp = 0.05 * cur_cost / math.log(2)
    cooling = (0.01 / temp) ** (1 / iterations)
    qmin, qmax = max(2, inst.n // 10), max(3, int(0.3 * inst.n))
    history = []
    t0 = time.perf_counter()

    for it in range(iterations):
        i = rng.choice(len(destroy_ops), p=w_d / w_d.sum())
        j = rng.choice(len(repair_ops), p=w_r / w_r.sum())
        q = int(rng.integers(qmin, qmax + 1))

        cand = current.copy()
        removed = destroy_ops[i](cand, q, rng)
        cand.remove(removed)
        repair_ops[j](cand, removed)
        cand_cost = cand.cost()

        score = 0
        if cand_cost < best_cost - 1e-9:
            best, best_cost = cand.copy(), cand_cost
            current, cur_cost = cand, cand_cost
            score = 33
        elif cand_cost < cur_cost - 1e-9:
            current, cur_cost = cand, cand_cost
            score = 9
        elif rng.random() < math.exp(-(cand_cost - cur_cost) / temp):
            current, cur_cost = cand, cand_cost
            score = 13

        s_d[i] += score
        s_r[j] += score
        n_d[i] += 1
        n_r[j] += 1
        if (it + 1) % segment == 0:
            w_d = (1 - reaction) * w_d + reaction * np.where(n_d > 0, s_d / np.maximum(n_d, 1), 0) + 1e-3
            w_r = (1 - reaction) * w_r + reaction * np.where(n_r > 0, s_r / np.maximum(n_r, 1), 0) + 1e-3
            s_d[:], s_r[:], n_d[:], n_r[:] = 0, 0, 0, 0

        temp *= cooling
        history.append(best_cost)

    return best.routes, history, time.perf_counter() - t0
