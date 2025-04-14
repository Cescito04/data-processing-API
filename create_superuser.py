import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'data_processing_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()

def create_superuser():
    try:
        if not User.objects.filter(username='bruceWayne').exists():
            User.objects.create_superuser(
                username='bruceWayne',
                email='batman@dark-knight.com',
                password='marvel221'
            )
            print('Superuser créé avec succès!')
        else:
            print('Le superutilisateur existe déjà.')
    except IntegrityError:
        print('Erreur: Le superutilisateur existe déjà.')
    except Exception as e:
        print(f'Erreur lors de la création du superutilisateur: {str(e)}')

if __name__ == '__main__':
    create_superuser()