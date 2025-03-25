# API de Traitement de Données

## Objectif
Créer une API REST pour le traitement et l'analyse de données, permettant aux utilisateurs d'effectuer des opérations statistiques sur des ensembles de données.

## Fonctionnalités

### Gestion des Données
- Upload de fichiers de données (CSV, JSON)
- Validation automatique des formats de données
- Détection et gestion des valeurs manquantes
- Identification et traitement des valeurs aberrantes
- Suppression des doublons
- Normalisation des données

### Analyses Statistiques
- Statistiques descriptives (moyenne, médiane, écart-type)
- Analyses de distribution
- Détection des corrélations
- Tests statistiques de base

### Visualisation
- Génération de graphiques (histogrammes, boîtes à moustaches)
- Export des visualisations en formats PNG/PDF
- Personnalisation des paramètres visuels

## Technologies
- Python 3.x
- FastAPI pour l'API REST
- Pandas pour le traitement des données
- NumPy pour les calculs statistiques
- Matplotlib/Seaborn pour les visualisations
- SQLite pour le stockage

## Structure du Projet
```
data-processing-API/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── routes/
│   │   └── data_routes.py    # Endpoints de l'API
│   ├── models/
│   │   └── data_models.py    # Modèles Pydantic
│   ├── services/
│   │   └── data_service.py   # Logique métier
│   └── utils/
│       └── data_processing.py # Fonctions utilitaires
├── tests/
│   ├── test_data_processing.py
│   └── test_data_service.py
├── data/
└── requirements.txt
```

## Installation
1. Cloner le repository
   ```bash
   git clone [url-du-repo]
   cd data-processing-API
   ```

2. Créer un environnement virtuel
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   .\venv\Scripts\activate  # Windows
   ```

3. Installer les dépendances
   ```bash
   pip install -r requirements.txt
   ```

4. Lancer l'API
   ```bash
   uvicorn app.main:app --reload
   ```

## Utilisation de l'API

### Upload de Données
```python
POST /api/v1/data/upload
Content-Type: multipart/form-data

# Réponse
{
    "status": "success",
    "file_id": "abc123",
    "rows_count": 1000
}
```

### Analyse Statistique
```python
GET /api/v1/data/{file_id}/stats

# Réponse
{
    "mean": 42.5,
    "median": 41.0,
    "std": 5.2,
    "missing_values": 10
}
```

## Tests
Les tests unitaires couvrent :
- Validation des données
- Traitement statistique
- Endpoints de l'API

Exécution des tests :
```bash
python -m pytest tests/
```

## Documentation API
La documentation complète de l'API est disponible sur `/docs` une fois le serveur lancé.
Elle inclut :
- Description détaillée des endpoints
- Schémas de requêtes/réponses
- Exemples d'utilisation
- Codes d'erreur

## Contribution
1. Fork le projet
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request