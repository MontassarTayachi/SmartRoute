# Guide d'utilisation - SmartRoute API

Ce guide explique comment lancer l'API, s'authentifier et utiliser les endpoints principaux (livraisons, tracking GPS, routes).

## 1) Prerequis

- Python 3.10+
- MongoDB accessible depuis l'application
- Fichier `.env` configure

## 2) Installation et demarrage

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API locale : `http://127.0.0.1:8000`
Swagger : `http://127.0.0.1:8000/docs`

## 3) Authentification

La majorite des endpoints proteges utilisent un token Bearer.

### Connexion

Endpoint : `POST /api/v1/auth/login`

Type de body : `application/x-www-form-urlencoded`

Champs :
- `username` (email utilisateur)
- `password`

Exemple cURL :

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=StrongP@ssw0rd"
```

Reponse :
- `access_token`
- `refresh_token`
- `token_type`

### Header a reutiliser

```text
Authorization: Bearer <access_token>
```

## 4) Module Deliveries

Base path : `/api/v1/deliveries`

### Lister les livraisons

`GET /api/v1/deliveries?status=pending&date=2026-07-08&page=1&limit=20`

Codes : `200`

### Creer une livraison

`POST /api/v1/deliveries`

```json
{
  "customer": "ACME",
  "pickup_address": "10 Rue de Rivoli, Paris",
  "pickup_address_lat": 48.8566,
  "pickup_address_lng": 2.3522,
  "dropoff_address": "25 Avenue des Champs-Elysees, Paris",
  "dropoff_address_lat": 48.8666,
  "dropoff_address_lng": 2.3722,
  "weight_kg": 125.5,
  "priority": "high",
  "scheduled_at": "2026-07-08T10:30:00Z"
}
```

Codes : `201`

### Detail livraison

`GET /api/v1/deliveries/{delivery_id}`

Codes : `200`

### Mise a jour partielle

`PUT /api/v1/deliveries/{delivery_id}`

Exemple body partiel :

```json
{
  "priority": "urgent",
  "weight_kg": 140.0
}
```

Codes : `200`

### Affecter vehicule + conducteur

`POST /api/v1/deliveries/{delivery_id}/assign`

```json
{
  "vehicle_id": "507f1f77bcf86cd799439011",
  "driver_id": "507f191e810c19729de860ea"
}
```

Codes : `200`

### Changer le statut

`POST /api/v1/deliveries/{delivery_id}/status`

```json
{
  "status": "in_progress"
}
```

Statuts autorises :
- `pending`
- `assigned`
- `in_progress`
- `delivered`
- `cancelled`

Codes : `200`

## 5) Affectation conducteur -> vehicule

Endpoint : `POST /api/v1/drivers/{driver_id}/assign_vehicle`

```json
{
  "vehicle_id": "507f1f77bcf86cd799439011"
}
```

Codes : `200`

## 6) Module GPS Locations

Base path : `/api/v1/locations`

### Ajouter une position GPS

`POST /api/v1/locations`

```json
{
  "vehicle_id": "507f1f77bcf86cd799439011",
  "lat": 48.8566,
  "lng": 2.3522,
  "speed_kmh": 42.3,
  "heading": 90,
  "timestamp": "2026-07-08T10:30:00Z"
}
```

Codes : `201`

## 7) Vehicules en direct

Endpoint : `GET /api/v1/vehicles/live`

Retour : derniere position de chaque vehicule (aggregation MongoDB).

Codes : `200`

## 8) Tracking GPS temps reel des vehicules

Base path : `/api/v1/vehicles/{vehicle_id}`

### Envoyer la position actuelle d'un vehicule

`POST /api/v1/vehicles/{vehicle_id}/location`

```json
{
  "latitude": 48.8566,
  "longitude": 2.3522,
  "timestamp": "2026-07-09T11:00:00Z"
}
```

Reponse type :

```json
{
  "vehicle_id": "507f1f77bcf86cd799439011",
  "vehicle_name": "Renault Master AB-123-CD",
  "driver_name": "Jean Dupont",
  "latitude": 48.8566,
  "longitude": 2.3522,
  "timestamp": "2026-07-09T11:00:00Z"
}
```

Codes : `200`, `404` si le vehicule n'existe pas.

### Recuperer la derniere position connue

`GET /api/v1/vehicles/{vehicle_id}/location`

Reponse type :

```json
{
  "vehicle_id": "507f1f77bcf86cd799439011",
  "vehicle_name": "Renault Master AB-123-CD",
  "driver_name": "Jean Dupont",
  "latitude": 48.8566,
  "longitude": 2.3522,
  "timestamp": "2026-07-09T11:00:00Z"
}
```

Codes : `200`, `404` si aucune position n'existe encore.

### Recuperer la derniere position de tous les vehicules

`GET /api/v1/vehicles/locations`

Reponse type :

```json
[
  {
    "vehicle_id": "507f1f77bcf86cd799439011",
    "vehicle_name": "Renault Master AB-123-CD",
    "driver_name": "Jean Dupont",
    "latitude": 48.8566,
    "longitude": 2.3522,
    "timestamp": "2026-07-09T11:00:00Z"
  }
]
```

Notes :
- `vehicle_name` et `driver_name` peuvent etre `null` si l'information n'est pas disponible.

Codes : `200`

### WebSocket de tracking en temps reel

`WS /api/v1/ws/vehicles/tracking`

Principe :
- connexion unique cote administrateur pour recevoir les updates de tous les vehicules
- a chaque nouvel appel POST location, la position est diffusee automatiquement a tous les clients connectes

Message diffuse :

```json
{
  "vehicle_id": "507f1f77bcf86cd799439011",
  "vehicle_name": "Renault Master AB-123-CD",
  "driver_name": "Jean Dupont",
  "latitude": 48.8566,
  "longitude": 2.3522,
  "timestamp": "2026-07-09T11:00:00Z"
}
```

Exemple URL locale :
- `ws://127.0.0.1:8000/api/v1/ws/vehicles/tracking`

Important :
- l'ancien WebSocket par vehicule `WS /api/v1/ws/vehicles/{vehicle_id}/tracking` n'est plus utilise.

### Stockage en base

Le backend enregistre automatiquement :
- la derniere position dans `vehicle_latest_locations`
- l'historique des positions dans `vehicle_location_history`

## 9) Module Routes

Base path : `/api/v1/routes`

### Historique des trajets

`GET /api/v1/routes/history?vehicle_id=<id>&from=2026-07-01T00:00:00Z&to=2026-07-08T23:59:59Z`

Codes : `200`

### Optimisation de route (v1 extensible)

`POST /api/v1/routes/optimiz`

```json
{
  "delivery_ids": [
    "507f191e810c19729de860ea",
    "507f1f77bcf86cd799439011"
  ],
  "constraints": {
    "avg_speed_kmh": 40
  }
}
```

Reponse type :

```json
{
  "route": [],
  "distance_km": 0,
  "estimated_time": 0
}
```

Codes : `200`

## 10) Erreurs API

Les erreurs suivantes sont gerees :
- `400` : ObjectId invalide / donnee invalide
- `404` : ressource introuvable
- `409` : conflit (exemple doublon)
- `500` : erreur base de donnees

## 11) Verification rapide post-deploiement

1. Ouvrir `http://127.0.0.1:8000/docs`
2. Verifier les nouveaux endpoints
3. Verifier les codes de retour :
   - POST creation : `201`
   - GET : `200`
   - PUT : `200`
