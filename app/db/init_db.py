from datetime import datetime
from pymongo import MongoClient, ASCENDING
from pymongo.errors import CollectionInvalid


def _create_collection_with_validator(db, name: str, validator: dict, indexes: list[tuple]):
    """Create a collection with JSON schema validation and indexes if missing."""
    if name not in db.list_collection_names():
        db.create_collection(name, validator=validator)
    else:
        db.command({
            "collMod": name,
            "validator": validator,
            "validationLevel": "moderate",
        })

    for index in indexes:
        keys, kwargs = index
        db[name].create_index(keys, **kwargs)


def _users_validator() -> dict:
    return {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["name", "email", "password_hash", "role", "is_active", "created_at", "updated_at"],
            "properties": {
                "name": {"bsonType": "string", "description": "Nom complet de l'utilisateur."},
                "email": {"bsonType": "string", "pattern": "^.+@.+$", "description": "Email unique de l'utilisateur."},
                "password_hash": {"bsonType": "string", "description": "Hash bcrypt du mot de passe."},
                "role": {
                    "enum": ["admin", "dispatcher", "driver", "viewer"],
                    "description": "Rôle de l'utilisateur dans la plateforme.",
                },
                "is_active": {"bsonType": "bool", "description": "Statut active/inactive (soft delete)."},
                "created_at": {"bsonType": "date", "description": "Date de création du compte."},
                "updated_at": {"bsonType": "date", "description": "Date de dernière modification."},
            },
        }
    }


def _vehicles_validator() -> dict:
    return {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["registration", "vehicle_list_id", "capacity_kg", "status", "avg_fuel_consumption", "created_at"],
            "properties": {
                "registration": {"bsonType": "string", "description": "Immatriculation unique du véhicule."},
                "vehicle_list_id": {"bsonType": "objectId", "description": "Référence au type de véhicule (collection vehicleListe)."},
                "capacity_kg": {"bsonType": "int", "minimum": 0, "description": "Capacité de charge en kilogrammes."},
                "status": {
                    "enum": ["available", "in_use", "maintenance", "out_of_service"],
                    "description": "État opérationnel du véhicule.",
                },
                "avg_fuel_consumption": {
                    "bsonType": ["double", "int"],
                    "minimum": 0,
                    "description": "Consommation moyenne de carburant du véhicule.",
                },
                "created_at": {"bsonType": "date", "description": "Date d'enregistrement du véhicule."},
                "updated_at": {"bsonType": ["date", "null"], "description": "Date de dernière mise à jour."},
            },
        }
    }


def _drivers_validator() -> dict:
    return {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["full_name", "phone", "license_number", "availability"],
            "properties": {
                "full_name": {"bsonType": "string", "description": "Nom complet du conducteur."},
                "phone": {"bsonType": "string", "description": "Numéro de téléphone du conducteur."},
                "license_number": {"bsonType": "string", "description": "Numéro de permis unique du conducteur."},
                "availability": {
                    "bsonType": ["bool", "string"],
                    "enum": [True, False, "available", "unavailable"],
                    "description": "Disponibilité du conducteur pour l'affectation.",
                },
                "assigned_vehicle_id": {"bsonType": ["objectId", "null"], "description": "Référence facultative au véhicule assigné."},
                "login_user_id": {"bsonType": ["objectId", "null"], "description": "Référence à l'utilisateur (rôle driver) pour la connexion."},
                "assignment_history": {
                    "bsonType": "array",
                    "items": {
                        "bsonType": "object",
                        "properties": {
                            "vehicle_id": {"bsonType": "objectId"},
                            "assigned_at": {"bsonType": "date"},
                            "released_at": {"bsonType": ["date", "null"]},
                        },
                    },
                    "description": "Historique des affectations de véhicules.",
                },
            },
        }
    }


def _deliveries_validator() -> dict:
    return {
        "$jsonSchema": {
            "bsonType": "object",
            "required": [
                "reference",
                "customer",
                "pickup_address",
                "pickup_address_lat",
                "pickup_address_lng",
                "dropoff_address",
                "dropoff_address_lat",
                "dropoff_address_lng",
                "status",
                "priority",
                "weight_kg",
                "scheduled_at",
                "created_at",
                "updated_at",
            ],
            "properties": {
                "reference": {"bsonType": "string", "description": "Référence unique de la livraison."},
                "customer": {"bsonType": "string", "description": "Client destinataire de la livraison."},
                "pickup_address": {"bsonType": "string", "description": "Adresse textuelle de prise en charge."},
                "pickup_address_lat": {"bsonType": ["double", "int"], "minimum": -90, "maximum": 90, "description": "Latitude de prise en charge."},
                "pickup_address_lng": {"bsonType": ["double", "int"], "minimum": -180, "maximum": 180, "description": "Longitude de prise en charge."},
                "dropoff_address": {"bsonType": "string", "description": "Adresse textuelle de livraison."},
                "dropoff_address_lat": {"bsonType": ["double", "int"], "minimum": -90, "maximum": 90, "description": "Latitude de livraison."},
                "dropoff_address_lng": {"bsonType": ["double", "int"], "minimum": -180, "maximum": 180, "description": "Longitude de livraison."},
                "status": {
                    "enum": ["pending", "assigned", "picked", "in_progress", "delivered", "cancelled"],
                    "description": "Statut de la livraison.",
                },
                "priority": {"bsonType": "string", "description": "Priorité de la livraison."},
                "weight_kg": {"bsonType": ["double", "int"], "minimum": 0, "description": "Poids total de la livraison en kg."},
                "vehicle_id": {"bsonType": ["objectId", "null"], "description": "Référence du véhicule responsable."},
                "driver_id": {"bsonType": ["objectId", "null"], "description": "Référence du conducteur responsable."},
                "scheduled_at": {"bsonType": "date", "description": "Date/heure prévue de départ."},
                "delivered_at": {"bsonType": ["date", "null"], "description": "Date/heure de livraison effective."},
                "created_at": {"bsonType": "date", "description": "Date de création de la livraison."},
                "updated_at": {"bsonType": "date", "description": "Date de dernière modification de la livraison."},
            },
        }
    }


def _locations_validator() -> dict:
    return {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["vehicle_id", "lat", "lng", "speed_kmh", "heading", "timestamp"],
            "properties": {
                "vehicle_id": {"bsonType": "objectId", "description": "Référence du véhicule pour la télémétrie."},
                "lat": {"bsonType": "double", "minimum": -90, "maximum": 90, "description": "Latitude GPS."},
                "lng": {"bsonType": "double", "minimum": -180, "maximum": 180, "description": "Longitude GPS."},
                "speed_kmh": {"bsonType": ["double", "int"], "minimum": 0, "description": "Vitesse en km/h."},
                "heading": {"bsonType": ["double", "int"], "minimum": 0, "maximum": 360, "description": "Cap du véhicule en degrés."},
                "timestamp": {"bsonType": "date", "description": "Horodatage de la position."},
            },
        }
    }


def _vehicle_latest_locations_validator() -> dict:
    return {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["vehicle_id", "latitude", "longitude", "timestamp", "created_at", "updated_at"],
            "properties": {
                "vehicle_id": {"bsonType": "objectId", "description": "Référence du véhicule."},
                "latitude": {"bsonType": ["double", "int"], "minimum": -90, "maximum": 90, "description": "Latitude GPS."},
                "longitude": {"bsonType": ["double", "int"], "minimum": -180, "maximum": 180, "description": "Longitude GPS."},
                "timestamp": {"bsonType": "date", "description": "Horodatage envoyé par le véhicule."},
                "created_at": {"bsonType": "date", "description": "Date de création de l'entrée latest."},
                "updated_at": {"bsonType": "date", "description": "Date de mise à jour de l'entrée latest."},
            },
        }
    }


def _vehicle_location_history_validator() -> dict:
    return {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["vehicle_id", "latitude", "longitude", "timestamp", "created_at"],
            "properties": {
                "vehicle_id": {"bsonType": "objectId", "description": "Référence du véhicule."},
                "latitude": {"bsonType": ["double", "int"], "minimum": -90, "maximum": 90, "description": "Latitude GPS."},
                "longitude": {"bsonType": ["double", "int"], "minimum": -180, "maximum": 180, "description": "Longitude GPS."},
                "timestamp": {"bsonType": "date", "description": "Horodatage envoyé par le véhicule."},
                "created_at": {"bsonType": "date", "description": "Date d'insertion dans l'historique."},
            },
        }
    }


def _routes_validator() -> dict:
    return {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["vehicle_id", "delivery_ids", "planned_path", "actual_path", "distance_km", "estimated_duration_min"],
            "properties": {
                "vehicle_id": {"bsonType": "objectId", "description": "Référence du véhicule pour cet itinéraire."},
                "delivery_ids": {
                    "bsonType": "array",
                    "items": {"bsonType": "objectId"},
                    "description": "Liste des livraisons incluses dans la route.",
                },
                "planned_path": {"bsonType": "array", "items": {"bsonType": "object"}, "description": "Trajet planifié sous forme de points géographiques."},
                "actual_path": {"bsonType": "array", "items": {"bsonType": "object"}, "description": "Trajet réel suivi par le véhicule."},
                "distance_km": {"bsonType": ["double", "int"], "minimum": 0, "description": "Distance estimée ou réelle en km."},
                "estimated_duration_min": {"bsonType": ["double", "int"], "minimum": 0, "description": "Durée estimée en minutes."},
                "actual_duration_min": {"bsonType": ["double", "int", "null"], "minimum": 0, "description": "Durée réelle en minutes, si disponible."},
            },
        }
    }


def _predictions_validator() -> dict:
    return {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["route_id", "model_name", "model_version", "features", "predicted_duration_min", "predicted_distance_km", "confidence", "created_at"],
            "properties": {
                "route_id": {"bsonType": "objectId", "description": "Référence de l'itinéraire prédit."},
                "model_name": {"bsonType": "string", "description": "Nom du modèle utilisé."},
                "model_version": {"bsonType": "string", "description": "Version du modèle."},
                "features": {"bsonType": "object", "description": "Données d'entrée du modèle."},
                "predicted_duration_min": {"bsonType": ["double", "int"], "minimum": 0, "description": "Durée prédite en minutes."},
                "predicted_distance_km": {"bsonType": ["double", "int"], "minimum": 0, "description": "Distance prédite en km."},
                "confidence": {
                    "bsonType": ["double", "int"],
                    "minimum": 0,
                    "maximum": 1,
                    "description": "Niveau de confiance de la prédiction entre 0 et 1.",
                },
                "created_at": {"bsonType": "date", "description": "Date de création de la prédiction."},
            },
        }
    }


def _vehicle_liste_validator() -> dict:
    return {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["nom", "created_at"],
            "properties": {
                "nom": {"bsonType": "string", "description": "Nom du type de véhicule."},
                "image_url": {"bsonType": ["string", "null"], "description": "URL ou chemin de l'image du véhicule."},
                "created_at": {"bsonType": "date", "description": "Date de création."},
                "updated_at": {"bsonType": ["date", "null"], "description": "Date de dernière mise à jour."},
            },
        }
    }


def _region_settings_validator() -> dict:
    return {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["n_clusters", "mode", "updated_at"],
            "properties": {
                "n_clusters": {"bsonType": "int", "minimum": 1, "description": "Nombre de regions à générer."},
                "mode": {"enum": ["fixe", "auto"], "description": "Mode de calcul du nombre de regions."},
                "updated_by": {"bsonType": ["objectId", "null"], "description": "Utilisateur ayant modifié le paramétrage."},
                "updated_at": {"bsonType": "date", "description": "Date de mise à jour du paramétrage."},
            },
        }
    }


def _region_geometry_validator() -> dict:
    return {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["region_id", "center_lat", "center_lng", "radius_km", "computed_at"],
            "properties": {
                "region_id": {"bsonType": "int", "minimum": 0, "description": "Identifiant de la region."},
                "center_lat": {"bsonType": ["double", "int"], "description": "Latitude du centre de region."},
                "center_lng": {"bsonType": ["double", "int"], "description": "Longitude du centre de region."},
                "radius_km": {"bsonType": ["double", "int"], "minimum": 0, "description": "Rayon de la region en kilomètres."},
                "computed_at": {"bsonType": "date", "description": "Date de calcul des geometries."},
            },
        }
    }


def _algorithm_settings_validator() -> dict:
    return {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["algorithm_name", "is_active", "parameters", "updated_at"],
            "properties": {
                "algorithm_name": {"bsonType": "string", "description": "Nom de l'algorithme d'affectation."},
                "is_active": {"bsonType": "bool", "description": "Indique si l'algorithme est actif."},
                "parameters": {"bsonType": "object", "description": "Paramètres JSON spécifiques à l'algorithme."},
                "updated_by": {"bsonType": ["objectId", "null"], "description": "Utilisateur ayant modifié l'algorithme."},
                "updated_at": {"bsonType": "date", "description": "Date de mise à jour de l'algorithme."},
            },
        }
    }


def initialize_database(mongo_uri: str, db_name: str):
    """Initialize the smartRoute database with all collections, validators and indexes."""
    client = MongoClient(mongo_uri)
    db = client[db_name]

    collections = [
        (
            "users",
            _users_validator(),
            [
                ([("email", ASCENDING)], {"unique": True, "name": "unique_email"}),
            ],
        ),
        (
            "vehicles",
            _vehicles_validator(),
            [
                ([("registration", ASCENDING)], {"unique": True, "name": "unique_registration"}),
            ],
        ),
        (
            "drivers",
            _drivers_validator(),
            [
                ([("license_number", ASCENDING)], {"unique": True, "name": "unique_license_number"}),
                ([("login_user_id", ASCENDING)], {"unique": True, "sparse": True, "name": "unique_login_user_id"}),
            ],
        ),
        (
            "deliveries",
            _deliveries_validator(),
            [
                ([("reference", ASCENDING)], {"unique": True, "name": "unique_reference"}),
                ([("vehicle_id", ASCENDING)], {"name": "idx_vehicle_id"}),
                ([("driver_id", ASCENDING)], {"name": "idx_driver_id"}),
                ([("status", ASCENDING)], {"name": "idx_status"}),
            ],
        ),
        (
            "locations",
            _locations_validator(),
            [
                ([("vehicle_id", ASCENDING), ("timestamp", ASCENDING)], {"name": "idx_vehicle_timestamp"}),
            ],
        ),
        (
            "vehicle_latest_locations",
            _vehicle_latest_locations_validator(),
            [
                ([("vehicle_id", ASCENDING)], {"name": "idx_vehicle_latest_vehicle_id", "unique": True}),
                ([("timestamp", ASCENDING)], {"name": "idx_vehicle_latest_timestamp"}),
            ],
        ),
        (
            "vehicle_location_history",
            _vehicle_location_history_validator(),
            [
                ([("vehicle_id", ASCENDING), ("timestamp", ASCENDING)], {"name": "idx_vehicle_history_vehicle_timestamp"}),
            ],
        ),
        (
            "routes",
            _routes_validator(),
            [
                ([("vehicle_id", ASCENDING)], {"name": "idx_routes_vehicle_id"}),
            ],
        ),
        (
            "predictions",
            _predictions_validator(),
            [
                ([("route_id", ASCENDING)], {"name": "idx_predictions_route_id"}),
            ],
        ),
        (
            "vehicleListe",
            _vehicle_liste_validator(),
            [
                ([("nom", ASCENDING)], {"name": "idx_nom"}),
            ],
        ),
        (
            "region_settings",
            _region_settings_validator(),
            [
                ([("updated_at", ASCENDING)], {"name": "idx_region_settings_updated_at"}),
            ],
        ),
        (
            "region_geometry",
            _region_geometry_validator(),
            [
                ([("region_id", ASCENDING)], {"name": "unique_region_geometry_region_id", "unique": True}),
                ([("computed_at", ASCENDING)], {"name": "idx_region_geometry_computed_at"}),
            ],
        ),
        (
            "algorithm_settings",
            _algorithm_settings_validator(),
            [
                ([("algorithm_name", ASCENDING)], {"name": "unique_algorithm_name", "unique": True}),
                ([("is_active", ASCENDING)], {"name": "idx_algorithm_active"}),
            ],
        ),
    ]

    for name, validator, indexes in collections:
        try:
            _create_collection_with_validator(db, name, validator, indexes)
        except CollectionInvalid:
            db.create_collection(name)
            _create_collection_with_validator(db, name, validator, indexes)

    now = datetime.utcnow()
    if db.region_settings.count_documents({}) == 0:
        db.region_settings.insert_one({
            "n_clusters": 5,
            "mode": "fixe",
            "updated_by": None,
            "updated_at": now,
        })

    if db.algorithm_settings.count_documents({}) == 0:
        db.algorithm_settings.insert_many([
            {
                "algorithm_name": "greedy_capacity",
                "is_active": True,
                "parameters": {},
                "updated_by": None,
                "updated_at": now,
            },
            {
                "algorithm_name": "balanced_load",
                "is_active": False,
                "parameters": {},
                "updated_by": None,
                "updated_at": now,
            },
        ])

    # Optionally create an admin user placeholder if none exists.
    client.close()
