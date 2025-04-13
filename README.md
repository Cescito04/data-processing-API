# Application de Traitement de Données

Une application web Django pour le traitement et l'analyse de fichiers de données (CSV, JSON, XML) avec une interface d'administration personnalisée.

## Fonctionnalités Principales

### Gestion des Fichiers
- Upload de fichiers CSV, JSON et XML
- Validation automatique du format et de la structure
- Traitement des données avec détection des valeurs manquantes et aberrantes
- Export des données traitées en différents formats
- Interface utilisateur intuitive et responsive

### Interface d'Administration
- Tableau de bord personnalisé
- Gestion des utilisateurs et des permissions
- Suivi des fichiers traités avec indicateurs visuels
- Statistiques détaillées sur les données

## Prérequis

- Python 3.8+
- Django 4.2+
- Docker et Docker Compose (pour le déploiement)

## Installation

### Installation avec Docker

1. Cloner le repository :
```bash
git clone [url-du-repo]
cd data_processing_app
```

2. Construire et démarrer les conteneurs :
```bash
# Construire les images Docker
docker-compose build

# Démarrer les conteneurs en arrière-plan
docker-compose up -d

# Voir les logs des conteneurs
docker-compose logs -f

# Arrêter les conteneurs
docker-compose down
```

3. Exécuter les migrations et créer un superutilisateur :
```bash
# Appliquer les migrations
docker-compose exec web python manage.py migrate

# Créer un superutilisateur
docker-compose exec web python manage.py createsuperuser
```

4. Commandes Docker utiles :
```bash
# Accéder au shell du conteneur
docker-compose exec web bash

# Voir l'état des conteneurs
docker-compose ps

# Redémarrer les services
docker-compose restart

# Supprimer les conteneurs et les volumes
docker-compose down -v
```

### Installation Locale

1. Créer un environnement virtuel :
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate    # Windows
```

2. Installer les dépendances :
```bash
pip install -r requirements.txt
```

3. Configurer la base de données :
```bash
python manage.py migrate
```

4. Créer un superutilisateur :
```bash
python manage.py createsuperuser
```

5. Lancer le serveur :
```bash
python manage.py runserver
```

## Structure du Projet

```
data_processing_app/
├── app/                    # Application principale
│   ├── models/            # Modèles de données
│   ├── routes/            # Routes API
│   ├── services/          # Services métier
│   └── utils/             # Utilitaires de traitement
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

1. Accéder à l'interface d'administration :
   - URL : `http://localhost:8000/admin`
   - Connectez-vous avec vos identifiants superutilisateur

2. Upload et traitement de fichiers :
   - Formats supportés : CSV, JSON, XML
   - Taille maximale : 10MB
   - Validation automatique des données

3. Visualisation des résultats :
   - Statistiques descriptives
   - Détection des anomalies
   - Export des données traitées

## Fonctionnalités de l'Interface Admin

- Gestion des fichiers uploadés
- Suivi du statut de traitement
- Statistiques détaillées :
  - Nombre de lignes/colonnes
  - Valeurs manquantes
  - Valeurs aberrantes
  - Résumé du traitement

## Sécurité

- Authentification requise
- Validation des fichiers uploadés
- Protection contre les attaques CSRF
- Gestion des permissions utilisateurs

## Contribution

1. Forker le projet
2. Créer une branche pour votre fonctionnalité
3. Commiter vos changements
4. Pousser vers la branche
5. Créer une Pull Request

## Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.