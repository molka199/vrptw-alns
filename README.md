# VRPTW — Clarke-Wright + ALNS vs OR-Tools

Résolution heuristique du **problème de tournées de véhicules avec capacités et fenêtres de temps (VRPTW)**, et comparaison à un solveur de référence.

## Problème

- Un dépôt et *n* clients, chacun avec une demande, une fenêtre de temps `[ready, due]` et un temps de service.
- Flotte homogène de capacité *Q*. Chaque tournée part du dépôt et y revient avant la fin de l'horizon.
- **Objectif** : minimiser la distance totale parcourue.

Les instances sont générées dans l'esprit de Solomon. Le type **R** a des clients uniformes, le type **C** des clients en clusters. Chaque client est faisable seul par construction.

## Méthodes

| Méthode | Rôle |
|---|---|
| **Clarke-Wright** (`vrp/savings.py`) | Heuristique constructive des économies, adaptée aux fenêtres de temps. Fournit la solution initiale. |
| **ALNS** (`vrp/alns.py`) | *Adaptive Large Neighborhood Search* (Ropke & Pisinger, 2006). Opérateurs de destruction : aléatoire, pire coût, proximité (Shaw). Opérateurs de réparation : glouton, regret-2. Acceptation par recuit simulé et poids des opérateurs adaptés par segments de 100 itérations. |
| **OR-Tools** (`vrp/ortools_solver.py`) | Solveur de référence (Routing + Guided Local Search), avec le **même budget de temps** que l'ALNS. |

Deux choix d'implémentation :
- **Test d'insertion incrémental** : le décalage temporel est propagé jusqu'à ce que les dates redeviennent identiques, puis il s'arrête.
- **Cache des meilleures insertions** : seule la tournée modifiée est recalculée à chaque étape de réparation.

Toutes les solutions sont vérifiées par `check()` : couverture des clients, capacité et fenêtres de temps.

## Résultats

18 instances (R/C × 25, 50, 100 clients × 3 graines), ALNS à 3 000 itérations.

- **Gain moyen de l'ALNS par rapport à Clarke-Wright : 22 %**
- **Écart moyen par rapport à OR-Tools à temps égal : −1,9 %** (l'ALNS est meilleure en moyenne, jusqu'à −6 % sur 100 clients)
- Le temps d'exécution reste sous 25 s pour 100 clients.

Le détail est dans `results/results.md`, avec les figures de tournées et de convergence dans `results/`.

> OR-Tools avec une limite de temps courte n'est pas une borne optimale. La comparaison mesure la qualité **à budget de calcul égal**.

## Lancer

```bash
pip install -r requirements.txt
python run_experiments.py                          # toutes les instances (~4 min)
python run_experiments.py --sizes 25 --seeds 1     # test rapide
```

## Pistes d'extension

- **Deux échelons (2E-VRP)** : ajouter un hub, ce qui demande des opérateurs qui basculent une commande entre livraison directe et passage par le hub.
- **Bi-objectif** : approximer le front de Pareto, par exemple avec une méthode ε-contrainte autour de l'ALNS.
- **Réparation par programmation par contraintes** (CP-SAT) pour les contraintes difficiles (périssabilité, stocks).
- Évaluation sur les instances de benchmark de Solomon.
