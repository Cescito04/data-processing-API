# API de Traitement de Données

Une API Django robuste pour le traitement automatisé des données, permettant l'upload, le traitement et l'export de fichiers CSV et JSON.

## Fonctionnalités

### Gestion des Fichiers
- Upload de fichiers CSV et JSON
- Validation automatique du format des données
- Prévisualisation des données
- Export des données traitées en CSV, JSON ou Excel

### Traitement des Données
- Gestion des valeurs manquantes
  - Remplacement par la moyenne (données numériques)
  - Remplacement par la médiane (données numériques)
  - Remplacement par le mode (tous types de données)
- Traitement des valeurs aberrantes (outliers)
  - Méthode IQR (Interquartile Range)
  - Conservation des types de données d'origine
- Normalisation des données
  - Normalisation Min-Max [0,1]
  - Préservation des types de données entières
- Gestion des doublons
  - Détection et suppression automatique
- Support d'une colonne cible (pour l'apprentissage supervisé)

## Structure du Projet

```
data-processing-API/
├── data_processor/           # Application principale
│   ├── forms.py             # Formulaires de configuration
│   ├── models.py            # Modèles de données
│   ├── views.py             # Logique de traitement
│   └── urls.py              # Configuration des URLs
├── templates/               # Templates HTML
│   └── data_processor/      # Templates spécifiques
├── static/                  # Fichiers statiques
├── media/                   # Fichiers uploadés
│   └── uploads/            # Stockage des données
└── requirements.txt         # Dépendances
```

## Installation

1. Cloner le repository :
```bash
git clone [URL_DU_REPO]
cd data-processing-API
```

2. Créer un environnement virtuel et l'activer :
```bash
python -m venv venv
source venv/bin/activate  # Unix/macOS
# ou
venv\Scripts\activate  # Windows
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

## Utilisation

1. Accéder à l'interface web : `http://localhost:8000`

2. Upload de fichiers :
   - Formats supportés : CSV, JSON
   - Taille maximale : 10MB

3. Traitement des données :
   - Sélectionner le fichier à traiter
   - Configurer les options de traitement
   - Lancer le traitement

4. Export des résultats :
   - Choisir le format d'export (CSV, JSON, Excel)
   - Télécharger le fichier traité

## Endpoints API

- `GET /files/` : Liste des fichiers uploadés
- `POST /files/upload/` : Upload d'un nouveau fichier
- `GET /files/<id>/preview/` : Prévisualisation des données
- `POST /files/<id>/process/` : Traitement des données
- `GET /files/<id>/export/` : Export des données traitées
- `DELETE /files/<id>/` : Suppression d'un fichier

## Technologies Utilisées

- Django : Framework web
- Pandas : Traitement des données
- NumPy : Calculs numériques
- Bootstrap : Interface utilisateur

## Sécurité

- Validation des types de fichiers
- Limitation de la taille des fichiers
- Protection CSRF
- Gestion des permissions utilisateur

## Contribution

1. Fork le projet
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request