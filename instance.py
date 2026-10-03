from dataclasses import dataclass

import numpy as np


@dataclass
class Instance:
    name: str
    xy: np.ndarray
    demand: np.ndarray
    ready: np.ndarray
    due: np.ndarray
    service: np.ndarray
    capacity: int
    dist: np.ndarray

    @property
    def n(self):
        return len(self.xy) - 1


def generate(n, seed, kind="R", capacity=200, horizon=1000.0):
    """Instance VRPTW type Solomon. Noeud 0 = dépôt.
    kind = "R" (clients uniformes) ou "C" (clients regroupés en clusters)."""
    rng = np.random.default_rng(seed)
    if kind == "C":
        centers = rng.uniform(15, 85, size=(max(2, n // 15), 2))
        pts = centers[rng.integers(len(centers), size=n)] + rng.normal(0, 6, size=(n, 2))
        pts = np.clip(pts, 0, 100)
    else:
        pts = rng.uniform(0, 100, size=(n, 2))

    xy = np.vstack([[50.0, 50.0], pts])
    dist = np.linalg.norm(xy[:, None] - xy[None], axis=2)
    demand = np.concatenate([[0], rng.integers(5, 31, size=n)])
    service = np.concatenate([[0.0], np.full(n, 10.0)])

    # fenêtre centrée sur un instant atteignable : chaque client est faisable seul
    earliest = dist[0, 1:]
    latest = horizon - dist[1:, 0] - service[1:]
    center = rng.uniform(earliest, latest)
    width = rng.uniform(60, 180, size=n)
    ready = np.concatenate([[0.0], np.maximum(0.0, center - width / 2)])
    due = np.concatenate([[horizon], np.minimum(latest, center + width / 2)])

    return Instance(f"{kind}{n}_s{seed}", xy, demand, ready, due, service, capacity, dist)
