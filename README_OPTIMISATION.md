# SmartRoute - Guide de fonctionnement de l'algorithme d'optimisation

Ce document explique le flux réel utilisé par le backend pour transformer des livraisons en missions planifiées, en tenant compte de la géographie, de la capacité des véhicules et de l'ordre optimal de livraison.

## 1. Objectif global

L'algorithme a pour but de :

- regrouper les livraisons par zone géographique,
- affecter les chauffeurs et véhicules disponibles à ces zones,
- répartir les livraisons selon la capacité des véhicules,
- calculer un ordre de passage respectant les contraintes de pickup/delivery,
- produire une mission avec distance, durée et polyline de trajet.

Le processus se base principalement sur les classes suivantes :

- `KMeansClusterer` pour le clustering géographique,
- `DriverAssignmentService` pour l'affectation des conducteurs aux régions,
- `CapacityOptimizer` pour la répartition des livraisons par capacité,
- `NearestNeighborOptimizer` pour l'optimisation locale de l'itinéraire,
- `RouteRefiner` pour le post-traitement `2-opt` / `Or-opt`,
- `OSMRoutingService` pour le calcul du trajet réel.

## 2. Comment l'algorithme fonctionne en pratique

L'algorithme fonctionne comme une chaîne de décisions successives :

1. Il lit les livraisons prévues pour une journée et récupère les chauffeurs et véhicules disponibles.
2. Il découpe les livraisons en groupes géographiques proches, afin d'éviter de traiter toutes les commandes comme un seul gros bloc.
3. Il associe chaque conducteur à la région la plus proche de sa position actuelle.
4. Il répartit ensuite les livraisons entre les véhicules disponibles selon leur capacité restante.
5. Pour chaque véhicule/conducteur, il construit un ordre logique de passage afin d'éviter les détours et de respecter l'ordre pickup → delivery.
6. Enfin, il calcule la distance totale et la durée estimée, puis peut demander un trajet routier réel via OSRM.

Autrement dit, l'algorithme ne "résout" pas tout d'un coup. Il travaille par étapes, de façon progressive, pour produire une solution rapide, cohérente et exploitable.

---

## 3. Flux complet de l'optimisation

### Étape 1 - Récupération des livraisons

Pour une date cible, le service récupère les livraisons :

- `scheduled_at` dans la journée,
- `status` dans `pending` ou `assigned`.

Ensuite, il charge aussi :

- les conducteurs disponibles,
- les véhicules disponibles.

### Étape 2 - Clustering des livraisons en régions

Le service de clustering construit un point représentatif pour chaque livraison :

- latitude du centre = moyenne entre pickup et dropoff,
- longitude du centre = moyenne entre pickup et dropoff.

Puis, il applique `KMeans` sur ces points afin de former des régions géographiques.

Le nombre de régions n'est plus figé dans le code. Il est lu depuis `region_settings` en base, avec un mode `fixe` ou `auto`.

Le résultat est un dictionnaire :

- `region_id -> liste des livraisons`

Cela permet de découper le volume de travail par zone plutôt que de traiter tous les points comme un unique gros ensemble.

### Étape 3 - Détermination des centres des régions

La méthode `get_cluster_centers()` renvoie les centres de gravité des clusters calculés par K-Means.

Ces centres servent ensuite à attribuer les chauffeurs aux zones les plus proches.

À la fin du clustering, le service persiste aussi `region_geometry` avec :

- `center_lat`, `center_lng`,
- `radius_km` calculé à partir des points du cluster,
- `computed_at`.

### Étape 4 - Affectation des chauffeurs aux régions

L'affectation des conducteurs se fait avec une logique de proximité :

- pour chaque conducteur, on prend sa position actuelle (`current_lat`, `current_lng`),
- on calcule sa distance au centre de chaque région,
- on l'assigne à la région la plus proche.

Dans une version plus poussée, le service trie les régions par charge de travail (nombre de livraisons) et affecte d'abord les conducteurs aux zones ayant le plus de livraisons.

### Étape 5 - Répartition des livraisons par capacité des véhicules

Une fois les conducteurs organisés par région, la `CapacityOptimizer` répartit les livraisons entre les véhicules.

Le principe est le suivant :

1. on associe chaque conducteur à son véhicule,
2. on trie les livraisons par poids décroissant,
3. on place chaque livraison dans le véhicule qui a encore la meilleure capacité restante,
4. on évite les assignments impossibles si la capacité est insuffisante.

Cette étape garantit qu'une livraison ne soit pas placée sur un véhicule trop petit pour la porter.

### Étape 6 - Optimisation de l'ordre des étapes

Pour chaque mission, le service crée une liste d'étapes de type :

- `pickup`,
- `delivery`.

Chaque livraison est donc représentée par deux points :

- point de ramassage,
- point de dépôt.

Ensuite, `NearestNeighborOptimizer` construit l'itinéraire. Son fonctionnement est :

1. on part du point de départ ou de la première livraison,
2. on calcul la distance entre la position actuelle et chaque étape non encore visitée,
3. on choisit l'étape la plus proche,
4. on la retire de la liste des étapes non visitées,
5. on répète tant qu'il reste des points.

Une règle de contrainte importante est respectée :

- une étape de `delivery` ne peut pas être choisie tant que son `pickup` correspondant n'a pas déjà été visité.

Cela évite un ordre logique invalide (livraison avant ramassage).

Après cette étape, `RouteRefiner` applique successivement `2-opt` puis `Or-opt` pour réduire les croisements et les détours locaux.

À chaque échange testé, la contrainte pickup/delivery est réévaluée. Tout mouvement qui viole l'ordre est rejeté, même s'il réduit la distance.

### Étape 7 - Calcul de la distance totale et durée estimée

La distance totale est calculée en sommant les distances entre chaque étape successive.

La durée estimée est obtenue avec une vitesse moyenne supposée de 30 km/h en zone urbaine.

### Étape 8 - Calcul du trajet réel via OSRM

Une fois l'ordre des étapes défini, le service envoie les coordonnées au service `OSMRoutingService`.

Ce service appelle l'API OpenStreetMap Routing (OSRM) pour obtenir :

- la distance réelle,
- la durée réelle,
- la polyline (géométrie du trajet).

Si l'appel OSRM échoue, le système revient sur un calcul de secours basé sur la formule de Haversine.

---

## 7. Paramétrage administrateur et géométrie

### Réglages des régions

- `GET /api/admin/optimization/region-settings`
- `PUT /api/admin/optimization/region-settings`

Payload `PUT` :

```json
{
    "n_clusters": 5,
    "mode": "fixe"
}
```

Réponse : le document stocké en base, avec `updated_at` et `updated_by`.

### Algorithmes d'affectation

- `GET /api/admin/optimization/algorithms`
- `POST /api/admin/optimization/algorithms/activate`

Payload `POST` :

```json
{
    "algorithm_name": "balanced_load",
    "parameters": {}
}
```

Réponse : le document activé dans `algorithm_settings`.

### Géométrie des régions

- `GET /api/regions/geometry`

Réponse GeoJSON : `FeatureCollection` de points, avec `radius_km` en propriété pour dessiner les cercles côté client.

---

## 4. Algorithme en pseudo-code

### Clustering

```python
centroids = []
for delivery in deliveries:
    centroid = ((pickup_lat + dropoff_lat) / 2, (pickup_lng + dropoff_lng) / 2)
    centroids.append(centroid)

labels = KMeans.fit_predict(centroids)
```

### Affectation conducteur-région

```python
for driver in drivers:
    nearest_region = min(region_centers, key=lambda center: distance(driver, center))
    assign(driver, nearest_region)
```

### Répartition par capacité

```python
sorted_deliveries = sort(deliveries, key=weight, descending=True)

for delivery in sorted_deliveries:
    vehicle = best_vehicle_with_max_remaining_capacity(delivery.weight)
    if vehicle:
        assign(delivery, vehicle)
```

### Ordonnancement des étapes

```python
current_position = start_location or first_step
while unvisited_steps:
    nearest = argmin(distance(current_position, step) for step in unvisited_steps)
    if nearest is a delivery and pickup not yet visited:
        skip it
    append(nearest)
    current_position = nearest.coordinate
```

---

## 5. Ce que l'algorithme optimise réellement

L'optimisation cherche à réduire le coût global de la mission selon trois dimensions :

- la distance à parcourir,
- la charge de travail par région,
- la faisabilité par capacité des véhicules.

En pratique, il s'agit d'un schéma hybride :

- clustering pour séparer les zones,
- affectation gloutonne pour répartir les charges,
- voisin le plus proche pour construire une route raisonnable,
- calcul routier réel pour obtenir une estimation plus fiable.

---

## 6. Limites connues

L'algorithme est pratique et rapide, mais il reste heuristique :

- le `Nearest Neighbor` ne garantit pas l'optimum global,
- la répartition par capacité est gloutonne,
- l'estimation de durée dépend de la vitesse moyenne utilisée,
- la qualité des clusters dépend du nombre de régions fixé (`n_clusters`).

En revanche, il est bien adapté aux cas où il faut générer une solution cohérente et exploitable rapidement.

---

## 7. Résultat final

À la fin du processus, le système produit une mission contenant :

- `driver_id`,
- `vehicle_id`,
- `region_id`,
- `delivery_ids`,
- `deliveries_order`,
- `total_weight`,
- `route_distance`,
- `route_duration`,
- `polyline`.

C’est cette structure qui est ensuite stockée en base pour l’exécution réelle de la mission.
