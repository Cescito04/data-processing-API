# API de Traitement de Données

## Objectif
Créer une API REST pour le traitement et l'analyse de données, permettant aux utilisateurs d'effectuer des opérations statistiques sur des ensembles de données.

## Fonctionnalités
- Upload de fichiers de données (CSV, JSON)
- Calcul de statistiques descriptives
- Filtrage et transformation des données
- Visualisation des résultats

## Technologies
- Python 3.x
- FastAPI
- Pandas pour le traitement des données
- SQLite pour le stockage

## Structure du Projet
```
data-processing-API/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── routes/
│   ├── models/
│   ├── services/
│   └── utils/
├── tests/
├── data/
└── requirements.txt
```

## Installation
1. Cloner le repository
2. Créer un environnement virtuel
3. Installer les dépendances : `pip install -r requirements.txt`
4. Lancer l'API : `uvicorn app.main:app --reload`

## Documentation API
La documentation complète de l'API sera disponible sur `/docs` une fois le serveur lancé.