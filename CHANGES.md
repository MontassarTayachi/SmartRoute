# Changements — corrections de fondation & stratégies de tournée pluggables

Ce document résume les changements apportés au module d'optimisation de missions
(`app/algorithms/`, `app/services/`, `app/routers/`) et explique comment utiliser
les nouvelles fonctionnalités. Pour l'architecture complète du pipeline, voir
[README.md](README.md).

## Sommaire

- [1. Corrections de fondation](#1-corrections-de-fondation)
- [2. Stratégies de tournée pluggables](#2-stratégies-de-tournée-pluggables)
- [3. Comment choisir une stratégie de tournée (admin)](#3-comment-choisir-une-stratégie-de-tournée-admin)
- [4. Comment comparer deux stratégies avant activation](#4-comment-comparer-deux-stratégies-avant-activation)
- [5. Utilisation depuis le code Python](#5-utilisation-depuis-le-code-python)
- [6. Changements d'API à connaître (breaking changes)](#6-changements-dapi-à-connaître-breaking-changes)
- [7. Dette connue, non corrigée](#7-dette-connue-non-corrigée)

---

## 1. Corrections de fondation

### 1.1 `KMeansClusterer` ne mute plus son état entre deux appels

**Avant** : `fit_predict` réduisait `self.n_clusters` de façon permanente quand il y
avait moins de livraisons que de clusters demandés. Une instance réutilisée entre
deux lots de tailles différentes restait bloquée sur la valeur réduite.

**Après** : la valeur effective est calculée dans une variable locale à chaque
appel et n'écrase plus `self.n_clusters`. La valeur réellement utilisée est
consultable via `clusterer.last_effective_n_clusters`.

```python
clusterer = KMeansClusterer(n_clusters=5)
clusterer.fit_predict(small_batch)   # 2 coordonnées -> utilise 2 clusters
clusterer.fit_predict(large_batch)   # 10 coordonnées -> utilise bien 5 clusters
```

### 1.2 Les livraisons sans coordonnées ne sont plus placées à `(0.0, 0.0)`

**Avant** : une livraison sans pickup/dropoff valide était clusterisée à l'origine
géographique, créant un cluster artificiel.

**Après** : ces livraisons sont exclues du clustering. `cluster_deliveries`
retourne désormais un **tuple** :

```python
regions, deliveries_without_coordinates = clustering_service.cluster_deliveries(deliveries)
```

- `regions` : `dict[int, list[delivery]]` — inchangé dans sa forme.
- `deliveries_without_coordinates` : liste des livraisons exclues (coordonnées
  manquantes), à traiter comme non-affectées en aval.

### 1.3 Les livraisons non affectées sont maintenant remontées par le pipeline principal

`MissionService.generate_missions_for_date` (utilisé par `POST /api/missions/generate`,
la route de production quotidienne) calcule maintenant les livraisons non
affectées, qu'elles aient été exclues du clustering (1.2) ou qu'aucun conducteur
disponible n'ait pu les prendre en charge.

**⚠️ Breaking change** — voir [§6](#6-changements-dapi-à-connaître-breaking-changes).

### 1.4 Différences documentées entre `/api/missions/assign` et le pipeline principal

Deux différences de comportement existaient déjà entre la route manuelle
`POST /api/missions/assign` et `MissionService` ; elles sont maintenant
explicitement documentées en commentaire (dans le code et au [§7](#7-dette-connue-non-corrigée)) plutôt que
silencieusement corrigées :

- `/assign` priorise les régions les plus chargées (`optimize_driver_assignment`),
  volontairement, car c'est un flux d'affectation manuelle/à la demande.
- `/assign` n'appelle pas OSRM et persiste une estimation Haversine — dette
  connue, non corrigée sans validation produit explicite.

---

## 2. Stratégies de tournée pluggables

L'ordonnancement de tournée (l'ordre dans lequel un conducteur visite ses
pickups/deliveries) est maintenant pluggable, sur le même modèle que
`algorithm_settings` pour la répartition de capacité.

### Interface commune

```python
# app/algorithms/route_strategies.py
class RouteOptimizationStrategy(ABC):
    strategy_name = "base"

    def optimize(self, steps, start_location=None) -> dict:
        """Retourne {"steps": [...], "total_distance": float, "estimated_duration": int}"""
```

### Les deux stratégies disponibles

| `strategy_name`  | Classe                  | Fichier                                | Description |
|-------------------|--------------------------|-----------------------------------------|-------------|
| `clarke_wright`   | `SavingsRouteStrategy`   | `app/algorithms/route_strategies.py`    | **Par défaut / fallback.** Rapide, déterministe, sans dépendance externe. Construit une tournée par l'algorithme des économies de Clarke & Wright *et* une tournée par plus-proche-voisin, raffine les deux avec 2-opt/Or-opt, retourne la meilleure des deux. |
| `ortools_cvrp`    | `ORToolsRouteStrategy`   | `app/algorithms/ortools_strategy.py`    | Résout la tournée avec Google OR-Tools (contrainte pickup-avant-delivery). Paramètre `time_limit_seconds` (défaut 5s). Bascule automatiquement sur `clarke_wright` si le solveur échoue ou dépasse le temps limite. |

Les deux respectent toujours la contrainte : le pickup d'une livraison précède
toujours sa delivery dans la tournée finale.

---

## 3. Comment choisir une stratégie de tournée (admin)

### Lister les stratégies disponibles et voir laquelle est active

```
GET /api/admin/optimization/route-strategies
```

```json
{
  "items": [
    {"strategy_name": "clarke_wright", "is_active": true, "parameters": {}, "updated_at": "..."},
    {"strategy_name": "ortools_cvrp", "is_active": false, "parameters": {"time_limit_seconds": 5}, "updated_at": "..."}
  ]
}
```

### Activer une stratégie

```
POST /api/admin/optimization/route-strategies/activate
Content-Type: application/json
Authorization: Bearer <token admin>

{
  "strategy_name": "ortools_cvrp",
  "parameters": {"time_limit_seconds": 8}
}
```

Une fois activée, **toutes** les générations de mission (`/api/missions/generate`,
le scheduler quotidien, `/api/missions/assign`) utilisent cette stratégie —
`RouteOptimizerService` la résout automatiquement via la base de données à
chaque appel.

Ces deux routes nécessitent un utilisateur `role: admin` (décorateur
`@require_admin`), exactement comme `/algorithms` et `/algorithms/activate`
pour la capacité.

---

## 4. Comment comparer deux stratégies avant activation

`POST /api/missions/test-generate` accepte un paramètre optionnel
`route_strategy` qui force une stratégie **pour cette simulation uniquement**,
sans toucher au réglage actif en base :

```json
POST /api/missions/test-generate
{
  "date": "2026-08-10",
  "route_strategy": "ortools_cvrp",
  "route_strategy_parameters": {"time_limit_seconds": 3}
}
```

La réponse inclut, en plus du résumé habituel :

```json
{
  "route_strategy_used": "ortools_cvrp",
  "route_optimization_time_ms": 842.31,
  "assignments": [
    {
      "route_distance": 12.4,
      "estimated_duration": 1488,
      "deliveries_order": [
        {"delivery_id": "...", "step_type": "pickup", "order": 0},
        {"delivery_id": "...", "step_type": "delivery", "order": 1}
      ]
    }
  ]
}
```

Pour comparer objectivement les deux stratégies sur le même jeu de données réel,
appelle la route deux fois (une par stratégie) avec la même `date`, et compare
`total_distance` et `route_optimization_time_ms`.

---

## 5. Utilisation depuis le code Python

### Résoudre et utiliser une stratégie directement

```python
from app.algorithms.route_strategies import SavingsRouteStrategy
from app.algorithms.ortools_strategy import ORToolsRouteStrategy

strategy = SavingsRouteStrategy()
# ou : strategy = ORToolsRouteStrategy(parameters={"time_limit_seconds": 5})

result = strategy.optimize(steps, start_location=(48.8566, 2.3522))
# result["steps"], result["total_distance"], result["estimated_duration"]
```

### Via `RouteOptimizerService` (résolution automatique)

```python
from app.services.route_optimizer import RouteOptimizerService

# Sans db : utilise toujours SavingsRouteStrategy
route_optimizer = RouteOptimizerService()

# Avec db : résout la stratégie active en base (comme CapacityOptimizer(db))
route_optimizer = RouteOptimizerService(db)

result = route_optimizer.optimize_mission_route(deliveries, start_location=start)

# Pour forcer une stratégie précise sans toucher au réglage actif :
from app.algorithms.ortools_strategy import ORToolsRouteStrategy
result = route_optimizer.optimize_mission_route(
    deliveries, start_location=start, strategy=ORToolsRouteStrategy()
)
```

### Résoudre la stratégie active sans lancer d'optimisation

```python
from app.services.optimization_settings_service import OptimizationSettingsService

strategy = OptimizationSettingsService(db).resolve_route_strategy()
print(strategy.strategy_name)  # "clarke_wright" ou "ortools_cvrp"
```

---

## 6. Changements d'API à connaître (breaking changes)

### `MissionService.generate_missions_for_date` / `POST /api/missions/generate`

**Avant** :
```json
[
  {"driver_id": "...", "vehicle_id": "...", "delivery_ids": [...], "...": "..."}
]
```

**Après** :
```json
{
  "missions": [
    {"driver_id": "...", "vehicle_id": "...", "delivery_ids": [...], "...": "..."}
  ],
  "unassigned_delivery_ids": ["665f...", "665f..."]
}
```

Tout client qui traitait la réponse de `POST /api/missions/generate` comme un
tableau doit être adapté pour lire `response.missions`.

### `ClusteringService.cluster_deliveries`

**Avant** : retournait `dict[int, list[delivery]]`.
**Après** : retourne `tuple[dict[int, list[delivery]], list[delivery]]` — le
second élément est la liste des livraisons exclues pour coordonnées manquantes.

### `POST /api/missions/test-generate`

Extension additive (non-breaking) : chaque élément de `assignments` contient
maintenant `deliveries_order` (étapes ordonnées), et la réponse contient
`route_strategy_used` / `route_optimization_time_ms`.

---

## 7. Dette connue, non corrigée

Ces points ont été identifiés pendant ce travail mais volontairement **non
corrigés**, faute de validation produit explicite — ils sont documentés en
commentaire dans le code concerné :

- `POST /api/missions/assign` n'appelle pas OSRM (contrairement au pipeline
  principal) : `route_distance`/`estimated_duration` restent une estimation
  Haversine et `polyline` est toujours `null`.
- `tests/test_mission_integration.py` : 4 tests utilisent encore le pattern
  async Motor (`await mongodb.find().to_list()`), incompatible avec le code
  Flask/pymongo synchrone actuel (dette de la conversion FastAPI → Flask).
- `tests/test_route_refiner.py::test_two_opt_corrects_crossing_route` : échec
  pré-existant du 2-opt, sans rapport avec ce travail.
