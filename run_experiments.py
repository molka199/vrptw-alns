"""Compare Clarke-Wright, ALNS et OR-Tools (même budget de temps) sur des instances VRPTW générées."""
import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt

from vrp import alns, check, clarke_wright, generate, solve_ortools, total_cost

OUT = Path("results")


def plot_routes(inst, routes, title, path):
    fig, ax = plt.subplots(figsize=(6, 6))
    for r in routes:
        pts = inst.xy[[0] + r + [0]]
        ax.plot(pts[:, 0], pts[:, 1], "-o", ms=3, lw=1)
    ax.plot(*inst.xy[0], "ks", ms=9)
    ax.set_title(title)
    ax.set_aspect("equal")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def plot_convergence(history, ref, title, path):
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(history, label="ALNS (meilleure solution)")
    ax.axhline(ref, color="grey", ls="--", label="OR-Tools (même temps)")
    ax.set_xlabel("Itération")
    ax.set_ylabel("Distance totale")
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", type=int, nargs="+", default=[25, 50, 100])
    parser.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3])
    parser.add_argument("--iterations", type=int, default=3000)
    args = parser.parse_args()
    OUT.mkdir(exist_ok=True)

    rows = []
    for kind in ("R", "C"):
        for n in args.sizes:
            for seed in args.seeds:
                inst = generate(n, seed, kind)
                cw = clarke_wright(inst)
                routes, history, t = alns(inst, cw, iterations=args.iterations, seed=seed)
                ref = solve_ortools(inst, max(t, 1.0))
                for sol in (cw, routes, ref):
                    check(inst, sol)

                cw_cost, alns_cost, ref_cost = (total_cost(inst, s) for s in (cw, routes, ref))
                row = {
                    "instance": inst.name,
                    "cw": round(cw_cost, 1),
                    "alns": round(alns_cost, 1),
                    "ortools": round(ref_cost, 1),
                    "vehicles_alns": len(routes),
                    "vehicles_ortools": len(ref),
                    "gain_vs_cw_%": round(100 * (cw_cost - alns_cost) / cw_cost, 2),
                    "gap_vs_ortools_%": round(100 * (alns_cost - ref_cost) / ref_cost, 2),
                    "time_s": round(t, 1),
                }
                rows.append(row)
                print(row)

                if seed == args.seeds[0] and n == max(args.sizes):
                    plot_routes(inst, routes, f"ALNS - {inst.name} - {alns_cost:.1f}",
                                OUT / f"routes_{inst.name}.png")
                    plot_convergence(history, ref_cost, f"Convergence - {inst.name}",
                                     OUT / f"convergence_{inst.name}.png")

    with open(OUT / "results.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    with open(OUT / "results.md", "w") as f:
        f.write("| " + " | ".join(rows[0]) + " |\n")
        f.write("|" + "---|" * len(rows[0]) + "\n")
        for r in rows:
            f.write("| " + " | ".join(str(v) for v in r.values()) + " |\n")
        gain = sum(r["gain_vs_cw_%"] for r in rows) / len(rows)
        gap = sum(r["gap_vs_ortools_%"] for r in rows) / len(rows)
        f.write(f"\nGain moyen ALNS vs Clarke-Wright : {gain:.2f} %  \n")
        f.write(f"Écart moyen ALNS vs OR-Tools (négatif = ALNS meilleure) : {gap:.2f} %\n")
    print(f"\nGain moyen vs CW : {gain:.2f} % | écart moyen vs OR-Tools : {gap:.2f} %")


if __name__ == "__main__":
    main()
