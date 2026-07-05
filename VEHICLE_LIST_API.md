# Collection vehicleListe - Guide d'Utilisation

## Description
La collection `vehicleListe` permet de gérer une liste de types de véhicules avec leurs images associées.

## Endpoints API

### Base URL
```
/api/v1/vehicle-list
```

### 1. Lister les éléments
**GET** `/`

Paramètres de requête:
- `page` (integer, défaut: 1): Numéro de la page
- `size` (integer, défaut: 10): Nombre d'éléments par page

**Réponse:**
```json
{
  "items": [
    {
      "_id": "507f1f77bcf86cd799439011",
      "nom": "Camion de livraison",
      "image_url": "/uploads/vehicles/vehicle_507f1f77bcf86cd799439012_truck.jpg",
      "created_at": "2024-01-15T10:30:00"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 10
}
```

---

### 2. Créer un élément (avec upload d'image)
**POST** `/`

**Paramètres (formulaire):**
- `nom` (string, requis): Nom du type de véhicule
- `image` (file, optionnel): Fichier image (JPG, PNG, etc.)

**Exemple avec cURL:**
```bash
curl -X POST "http://localhost:8000/api/v1/vehicle-list/" \
  -H "Authorization: Bearer <token>" \
  -F "nom=Camion de livraison" \
  -F "image=@/path/to/image.jpg"
```

**Réponse:**
```json
{
  "_id": "507f1f77bcf86cd799439011",
  "nom": "Camion de livraison",
  "image_url": "/uploads/vehicles/vehicle_507f1f77bcf86cd799439012_truck.jpg",
  "created_at": "2024-01-15T10:30:00"
}
```

---

### 3. Récupérer un élément par ID
**GET** `/{item_id}`

**Exemple:**
```bash
curl -X GET "http://localhost:8000/api/v1/vehicle-list/507f1f77bcf86cd799439011" \
  -H "Authorization: Bearer <token>"
```

**Réponse:**
```json
{
  "_id": "507f1f77bcf86cd799439011",
  "nom": "Camion de livraison",
  "image_url": "/uploads/vehicles/vehicle_507f1f77bcf86cd799439012_truck.jpg",
  "created_at": "2024-01-15T10:30:00"
}
```

---

### 4. Mettre à jour un élément
**PUT** `/{item_id}`

**Paramètres (formulaire):**
- `nom` (string, optionnel): Nouveau nom
- `image` (file, optionnel): Nouvelle image

**Exemple avec cURL:**
```bash
curl -X PUT "http://localhost:8000/api/v1/vehicle-list/507f1f77bcf86cd799439011" \
  -H "Authorization: Bearer <token>" \
  -F "nom=Camion de livraison Premium" \
  -F "image=@/path/to/new_image.jpg"
```

**Réponse:**
```json
{
  "_id": "507f1f77bcf86cd799439011",
  "nom": "Camion de livraison Premium",
  "image_url": "/uploads/vehicles/vehicle_507f1f77bcf86cd799439013_new_image.jpg",
  "created_at": "2024-01-15T10:30:00"
}
```

---

### 5. Supprimer un élément
**DELETE** `/{item_id}`

**Exemple avec cURL:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/vehicle-list/507f1f77bcf86cd799439011" \
  -H "Authorization: Bearer <token>"
```

**Réponse:**
- Code 204 (No Content): Suppression réussie

---

## Fonctionnalités

✅ **Gestion complète des images:**
- Upload d'images lors de la création
- Mise à jour d'image
- Suppression automatique de l'ancienne image lors de la mise à jour
- Suppression automatique de l'image lors de la suppression de l'élément

✅ **Stockage:**
- Images stockées dans le dossier `uploads/vehicles/`
- URL accessible via `/uploads/vehicles/{filename}`

✅ **Authentification:**
- Tous les endpoints requièrent une authentification (token Bearer)

✅ **Pagination:**
- Support de la pagination pour la listage

---

## Structure des fichiers créés

```
app/
  models/
    vehicle_list.py          # Modèle de données
  schemas/
    vehicle_list.py          # Schémas Pydantic
  services/
    vehicle_list_service.py  # Logique métier
  routers/
    vehicle_list.py          # Endpoints API

uploads/
  vehicles/                  # Dossier de stockage des images
```

---

## Notes importantes

1. **Authentification:** Assurez-vous d'inclure un token d'authentification valide dans les en-têtes `Authorization: Bearer <token>`.

2. **Chemin des images:** Les images sont stockées dans `uploads/vehicles/` et accessibles via `/uploads/vehicles/{filename}`.

3. **Formats acceptés:** Tous les formats d'image courants sont acceptés (JPG, PNG, GIF, WebP, etc.).

4. **Taille des fichiers:** Assurez-vous que votre serveur FastAPI accepte la taille des fichiers uploadés.

5. **Nettoyage:** Les anciennes images sont automatiquement supprimées lors de la mise à jour ou de la suppression d'un élément.
