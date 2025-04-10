# API de Traitement de Données

Une API robuste pour le traitement automatisé de fichiers de données (CSV, JSON, XML) avec interface web intégrée.

## Fonctionnalités Principales

### Gestion des Fichiers
- Upload de fichiers CSV, JSON et XML
- Validation automatique du format et de la structure des données
- Prévisualisation des données avec statistiques descriptives
- Export des données traitées en CSV, JSON ou Excel
- Interface utilisateur intuitive et responsive

### Traitement des Données
- Analyse automatique de la structure des fichiers
- Détection des valeurs manquantes
- Statistiques descriptives par colonne
- Traitement personnalisé pour chaque type de fichier

## Prérequis

- Python 3.8 ou supérieur
- Django 4.0 ou supérieur
- Base de données SQLite (incluse)

## Installation

1. Cloner le dépôt :
```bash
git clone [url-du-depot]
cd data-processing-API
```

2. Créer un environnement virtuel :
```bash
python -m venv venv
source venv/bin/activate  # Sur Unix/macOS
venv\Scripts\activate    # Sur Windows
```

3. Installer les dépendances :
```bash
pip install -r requirements.txt
```

4. Appliquer les migrations :
```bash
python manage.py migrate
```

5. Lancer le serveur de développement :
```bash
python manage.py runserver
```

## Structure du Projet

```
data-processing-API/
├── app/                    # Core application
│   ├── models/            # Modèles de données
│   ├── routes/            # Routes API
│   ├── services/          # Services métier
│   └── utils/             # Utilitaires
├── data_processor/        # Application Django
│   ├── forms.py           # Formulaires
│   ├── models.py          # Modèles
│   ├── views.py           # Vues
│   └── urls.py            # URLs
├── templates/             # Templates HTML
├── static/                # Fichiers statiques
├── media/                 # Fichiers uploadés
└── requirements.txt       # Dépendances
```

## Utilisation

1. Accéder à l'interface web via `http://localhost:8000`
2. Utiliser le bouton "Importer un fichier" pour uploader un fichier
3. Visualiser la liste des fichiers importés
4. Traiter les fichiers avec le bouton "Traiter"
5. Exporter les résultats dans le format souhaité

## Formats de Fichiers Supportés

### CSV
- Séparateur : virgule (,)
- Encodage : UTF-8
- En-têtes de colonnes requis

### JSON
- Format : Array d'objets
- Structure cohérente entre les objets

### XML
- Structure valide et bien formée
- Namespace supporté

## Sécurité

- Validation des types de fichiers
- Limite de taille des fichiers
- Protection CSRF
- Authentification requise pour l'accès

## Tests

Exécuter les tests unitaires :
```bash
python manage.py test
```

## Contribution

1. Fork le projet
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request