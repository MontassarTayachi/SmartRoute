# SmartRoute API

Projet backend FastAPI pour la gestion de flotte, livraisons et prédiction d'itinéraires.

## Installation

1. Copier `.env.example` en `.env` et adapter les variables.
2. Installer les dépendances :

```bash
pip install -r requirements.txt
```

## Démarrage

```bash
uvicorn app.main:app --reload
```

## Endpoints

- Authentification : `/api/v1/auth`
- Utilisateurs : `/api/v1/users`
- Véhicules : `/api/v1/vehicles`
- Conducteurs : `/api/v1/drivers`
- Livraisons : `/api/v1/deliveries`
- Positions GPS : `/api/v1/locations`
- Routes : `/api/v1/routes`

L’API expose la documentation Swagger à :

```text
http://127.0.0.1:8000/docs
```

## Guide d'utilisation

Le guide complet est disponible dans :

`GUIDE_UTILISATION.md`
