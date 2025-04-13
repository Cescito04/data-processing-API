from django.shortcuts import render, redirect
from django.views.generic import ListView
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, FileResponse, HttpResponse
from django.core.cache import cache
from django.core.cache import cache as django_cache
from .models import DataFile
from .forms import DataFileUploadForm, DataProcessingForm, UserRegistrationForm, LoginForm
import pandas as pd
import numpy as np
import os
import json

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Inscription réussie ! Bienvenue sur notre plateforme.')
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'auth/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(username=email, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Bienvenue {user.first_name} !')
                return redirect('dashboard')
            else:
                messages.error(request, 'Email ou mot de passe incorrect.')
    else:
        form = LoginForm()
    return render(request, 'auth/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'Vous avez été déconnecté avec succès.')
    return redirect('login')

@login_required
def dashboard(request):
    return render(request, 'auth/dashboard.html')

@login_required
def upload_file(request):
    if request.method == 'POST':
        form = DataFileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                file = request.FILES['file']
                file_extension = file.name.split('.')[-1].lower()
                
                # Sauvegarder le type de fichier d'origine
                data_file = form.save(commit=False)
                data_file.original_file_type = file_extension
                data_file.file_type = 'csv'  # Le type final sera toujours CSV après traitement
                data_file.user = request.user  # Associer le fichier à l'utilisateur connecté
                data_file.original_filename = file.name
                data_file.save()
                
                messages.success(request, 'Fichier importé avec succès.')
                return redirect('file_list')
            except Exception as e:
                messages.error(request, f'Erreur lors de l\'importation du fichier: {str(e)}')
                return redirect('upload_file')
    else:
        form = DataFileUploadForm()
    
    return render(request, 'data_processor/upload.html', {'form': form})

def process_features(df_features, target_data, cleaned_data, processing_summary):
    # Traitement des valeurs manquantes
    if cleaned_data['handle_missing']:
        for column in df_features.columns:
            # Identifier le type de colonne
            is_binary = df_features[column].dropna().isin([0, 1]).all()
            is_numeric = pd.api.types.is_numeric_dtype(df_features[column])
            
            strategy = cleaned_data['missing_strategy']
            
            if is_binary:
                # Variables binaires : remplacer par le mode (0 ou 1)
                fill_value = df_features[column].mode()[0]
                df_features[column] = df_features[column].fillna(fill_value).astype(int)
            elif is_numeric:
                # Variables numériques
                if strategy == 'mean':
                    fill_value = df_features[column].mean()
                elif strategy == 'median':
                    fill_value = df_features[column].median()
                else:  # mode
                    fill_value = df_features[column].mode()[0]
                
                # Conserver le type d'origine si possible
                if pd.api.types.is_integer_dtype(df_features[column]):
                    df_features[column] = df_features[column].fillna(round(fill_value)).astype(int)
                else:
                    df_features[column] = df_features[column].fillna(fill_value)
            else:
                # Variables catégorielles
                fill_value = df_features[column].mode()[0]
                df_features[column] = df_features[column].fillna(fill_value)
        
        processing_summary['missing_values'] = 'Traitées selon le type de variable'
    
    # Traitement des outliers (uniquement sur les features numériques)
    if cleaned_data['handle_outliers']:
        numeric_cols = df_features.select_dtypes(include=[np.number]).columns
        for column in numeric_cols:
            Q1 = df_features[column].quantile(0.25)
            Q3 = df_features[column].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5*IQR
            upper_bound = Q3 + 1.5*IQR
            
            # Ne pas modifier les valeurs si elles sont dans les bornes
            mask = (df_features[column] >= lower_bound) & (df_features[column] <= upper_bound)
            df_features[column] = np.where(mask, df_features[column], 
                                         df_features[column].clip(lower_bound, upper_bound))
            
            # Conserver le type d'origine
            if pd.api.types.is_integer_dtype(df_features[column]):
                df_features[column] = df_features[column].round().astype(int)
        
        processing_summary['outliers'] = 'Traitées avec la méthode IQR'
    
    # Normalisation Min-Max (évite les valeurs négatives)
    if cleaned_data['normalize_data']:
        numeric_cols = df_features.select_dtypes(include=[np.number]).columns
        for column in numeric_cols:
            min_val = df_features[column].min()
            max_val = df_features[column].max()
            if max_val != min_val:  # éviter la division par zéro
                df_features[column] = (df_features[column] - min_val) / (max_val - min_val)
                # Conserver le type si possible
                if pd.api.types.is_integer_dtype(df_features[column]):
                    df_features[column] = (df_features[column] * 100).round().astype(int)
        
        processing_summary['normalization'] = 'Normalisation Min-Max (0-1)'
    
    # Suppression des doublons (sur les features seulement)
    if cleaned_data['remove_duplicates']:
        initial_rows = len(df_features)
        df_features = df_features.drop_duplicates()
        processing_summary['duplicates'] = f'{initial_rows - len(df_features)} doublons supprimés'
    
    # Réintégrer la colonne cible si elle existe
    if target_data is not None:
        return pd.concat([df_features, target_data], axis=1)
    return df_features

@login_required
def process_file(request, pk):
    try:
        data_file = DataFile.objects.get(pk=pk)
    except DataFile.DoesNotExist:
        messages.error(request, 'Fichier non trouvé.')
        return redirect('file_list')
    
    if request.method == 'POST':
        form = DataProcessingForm(request.POST)
        if form.is_valid():
            try:
                # Définir une taille de chunk plus grande pour réduire le nombre d'opérations d'E/S
                CHUNK_SIZE = 50000  # Augmenté pour un meilleur équilibre mémoire/performance
                
                # Initialiser le DataFrame final et le compteur de lignes
                df_processed = None
                processing_summary = {}
                total_rows = 0
                
                # Compter le nombre total de lignes pour la barre de progression
                if data_file.file_type == 'csv':
                    total_rows = sum(1 for _ in open(data_file.file.path))
                else:
                    with open(data_file.file.path, 'r') as f:
                        total_rows = sum(1 for line in f if line.strip())
                
                # Fonction pour traiter un chunk de données
                def process_chunk(chunk_df, target_column=None, chunk_index=0):
                    if target_column and target_column in chunk_df.columns:
                        target_data = chunk_df[target_column]
                        df_features = chunk_df.drop(columns=[target_column])
                    else:
                        target_data = None
                        df_features = chunk_df.copy()
                    
                    # Calculer et mettre à jour la progression
                    progress = int((chunk_index * CHUNK_SIZE) / total_rows * 100)
                    django_cache.set(f'process_progress_{data_file.id}', progress, 300)
                    
                    return process_features(df_features, target_data, form.cleaned_data, processing_summary)
                
                # Chargement et traitement des données par chunks avec progression
                if data_file.file_type == 'csv':
                    for chunk_index, chunk in enumerate(pd.read_csv(data_file.file.path, chunksize=CHUNK_SIZE)):
                        processed_chunk = process_chunk(chunk, form.cleaned_data.get('target_column'), chunk_index)
                        if df_processed is None:
                            df_processed = processed_chunk
                        else:
                            # Utiliser un fichier temporaire pour stocker les résultats intermédiaires
                            temp_file = f'/tmp/processed_chunk_{data_file.id}_{chunk_index}.csv'
                            processed_chunk.to_csv(temp_file, index=False)
                            df_processed = pd.concat([df_processed, pd.read_csv(temp_file)])
                            os.remove(temp_file)  # Nettoyer le fichier temporaire
                else:
                    # Pour les fichiers JSON, utiliser un itérateur de lignes avec progression
                    chunk_data = []
                    processed_rows = 0
                    with open(data_file.file.path, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line:
                                try:
                                    chunk_data.append(json.loads(line))
                                    processed_rows += 1
                                    if len(chunk_data) >= CHUNK_SIZE:
                                        chunk_df = pd.DataFrame(chunk_data)
                                        processed_chunk = process_chunk(chunk_df, form.cleaned_data.get('target_column'), processed_rows // CHUNK_SIZE)
                                        
                                        # Utiliser un fichier temporaire pour les résultats intermédiaires
                                        temp_file = f'/tmp/processed_chunk_{data_file.id}_{processed_rows // CHUNK_SIZE}.csv'
                                        if df_processed is None:
                                            df_processed = processed_chunk
                                        else:
                                            processed_chunk.to_csv(temp_file, index=False)
                                            df_processed = pd.concat([df_processed, pd.read_csv(temp_file)])
                                            os.remove(temp_file)
                                        
                                        chunk_data = []
                                        
                                        # Mettre à jour la progression
                                        progress = int(processed_rows / total_rows * 100)
                                        django_cache.set(f'process_progress_{data_file.id}', progress, 300)
                                        
                                except json.JSONDecodeError as e:
                                    raise Exception(f"Erreur de parsing JSON à la ligne: {line}. {str(e)}")
                    
                    # Traiter le dernier chunk s'il existe
                    if chunk_data:
                        chunk_df = pd.DataFrame(chunk_data)
                        processed_chunk = process_chunk(chunk_df, form.cleaned_data.get('target_column'), processed_rows // CHUNK_SIZE)
                        if df_processed is None:
                            df_processed = processed_chunk
                        else:
                            temp_file = f'/tmp/processed_chunk_{data_file.id}_final.csv'
                            processed_chunk.to_csv(temp_file, index=False)
                            df_processed = pd.concat([df_processed, pd.read_csv(temp_file)])
                            os.remove(temp_file)
                
                
                # Sauvegarde du fichier traité avec mise en cache
                from django.core.cache import cache
                import tempfile
                
                # Utiliser un fichier temporaire pour la sauvegarde progressive
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    if data_file.file_type == 'csv':
                        # Sauvegarder par morceaux pour économiser la mémoire
                        for i in range(0, len(df_processed), CHUNK_SIZE):
                            chunk = df_processed.iloc[i:i+CHUNK_SIZE]
                            # Premier chunk : écrire avec l'en-tête
                            if i == 0:
                                chunk.to_csv(temp_file.name, mode='w', index=False)
                            # Chunks suivants : ajouter sans en-tête
                            else:
                                chunk.to_csv(temp_file.name, mode='a', header=False, index=False)
                            
                            # Mettre à jour la progression dans le cache
                            progress = int((i + len(chunk)) / len(df_processed) * 100)
                            django_cache.set(f'process_progress_{data_file.id}', progress, 300)
                    else:
                        # Pour JSON, sauvegarder ligne par ligne
                        with open(temp_file.name, 'w') as f:
                            for i, record in enumerate(df_processed.to_dict('records')):
                                json.dump(record, f)
                                f.write('\n')
                                
                                # Mettre à jour la progression tous les 1000 enregistrements
                                if i % 1000 == 0:
                                    progress = int(i / len(df_processed) * 100)
                                    django_cache.set(f'process_progress_{data_file.id}', progress, 300)
                    
                    # Déplacer le fichier temporaire vers l'emplacement final
                    processed_path = f'{data_file.file.path}_processed'
                    import shutil
                    shutil.move(temp_file.name, processed_path)
                
                # Mettre à jour les métadonnées
                data_file.processed = True
                data_file.processing_summary = processing_summary
                data_file.save()
                
                # Supprimer la progression du cache
                django_cache.delete(f'process_progress_{data_file.id}')
                
                messages.success(request, 'Données traitées avec succès!')
                return redirect('file_list')
            
            except Exception as e:
                messages.error(request, f'Erreur lors du traitement: {str(e)}')
                return redirect('process_file', pk=pk)
    else:
        form = DataProcessingForm()
    
    return render(request, 'data_processor/process.html', {
        'form': form,
        'data_file': data_file
    })


class FileListView(LoginRequiredMixin, ListView):
    model = DataFile
    template_name = 'data_processor/file_list.html'
    context_object_name = 'files'
    ordering = ['-upload_date']
    
    def get_queryset(self):
        return DataFile.objects.filter(user=self.request.user).order_by('-upload_date')


@login_required
def clear_all_files(request):
    try:
        # Récupérer tous les fichiers
        data_files = DataFile.objects.all()
        
        # Supprimer chaque fichier physique et son fichier traité
        for data_file in data_files:
            if os.path.exists(data_file.file.path):
                os.remove(data_file.file.path)
            
            processed_path = f'{data_file.file.path}_processed'
            if os.path.exists(processed_path):
                os.remove(processed_path)
        
        # Supprimer tous les enregistrements de la base de données
        data_files.delete()
        
        messages.success(request, 'Tous les fichiers ont été supprimés avec succès!')
    except Exception as e:
        messages.error(request, f'Erreur lors de la suppression des fichiers: {str(e)}')
    
    return redirect('file_list')


@login_required
def upload_file(request):
    if request.method == 'POST':
        form = DataFileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Récupérer le fichier uploadé
                uploaded_file = request.FILES['file']
                file_extension = uploaded_file.name.split('.')[-1].lower()
                
                # Créer le dossier media/uploads s'il n'existe pas
                import os
                from django.conf import settings
                upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
                os.makedirs(upload_dir, exist_ok=True)
                
                # Vérifier le type de fichier
                if file_extension not in ['csv', 'json', 'xml']:
                    messages.error(request, 'Type de fichier non supporté. Veuillez uploader un fichier CSV, JSON ou XML.')
                    return redirect('upload_file')
                
                # Créer l'instance de DataFile
                data_file = form.save(commit=False)
                data_file.user = request.user  # Associer l'utilisateur connecté
                data_file.original_filename = uploaded_file.name
                
                # Créer le chemin complet du fichier
                import datetime
                today = datetime.date.today()
                file_dir = os.path.join('uploads', str(today.year), str(today.month).zfill(2))
                upload_path = os.path.join(settings.MEDIA_ROOT, file_dir)
                os.makedirs(upload_path, exist_ok=True)
                
                # Définir le chemin du fichier relatif à MEDIA_ROOT
                data_file.file.field.upload_to = file_dir
                
                data_file.file_type = file_extension
                data_file.save()  # Sauvegarder d'abord le fichier
                
                # Si c'est un fichier XML, valider et convertir en CSV
                if file_extension == 'xml':
                    from app.utils.xml_processor import load_xml_data, validate_xml_structure
                    from app.utils.xml_validator import validate_xml_data
                    
                    # Lire le contenu du fichier XML
                    with open(data_file.file.path, 'r', encoding='utf-8') as xml_file:
                        xml_content = xml_file.read()
                    
                    # Valider la structure XML
                    is_valid_structure, root, structure_error = validate_xml_structure(xml_content)
                    if not is_valid_structure:
                        data_file.delete()  # Supprimer le fichier en cas d'erreur
                        raise ValueError(f"Structure XML invalide : {structure_error}")
                    
                    # Valider les données XML
                    is_valid_data, data_errors = validate_xml_data(xml_content)
                    if not is_valid_data:
                        data_file.delete()  # Supprimer le fichier en cas d'erreur
                        raise ValueError(f"Données XML invalides : {', '.join(data_errors)}")
                    
                    # Charger et convertir les données
                    df = load_xml_data(data_file.file.path)
                    if df is None:
                        data_file.delete()  # Supprimer le fichier en cas d'erreur
                        raise ValueError("Erreur lors de la conversion des données XML en DataFrame")
                    
                    # Sauvegarder en CSV
                    csv_path = data_file.file.path.rsplit('.', 1)[0] + '.csv'
                    df.to_csv(csv_path, index=False)
                    
                    # Mettre à jour le fichier et le type
                    data_file.file.name = csv_path
                    data_file.file_type = 'csv'
                    data_file.save()
                
                # Analyser le fichier pour obtenir les métadonnées
                try:
                    if file_extension == 'csv':
                        df = pd.read_csv(data_file.file.path)
                    elif file_extension == 'json':
                        from app.utils.json_processor import load_json_data
                        df = load_json_data(data_file.file.path)
                        if df is None:
                            raise ValueError("Erreur lors du chargement du fichier JSON")
                    
                    # Mettre à jour les métadonnées
                    data_file.row_count = len(df)
                    data_file.column_count = len(df.columns)
                    
                    # Calculer les statistiques sur les valeurs manquantes
                    missing_values = {}
                    for column in df.columns:
                        missing_count = df[column].isnull().sum()
                        if missing_count > 0:
                            missing_values[column] = int(missing_count)
                    data_file.missing_values = missing_values
                    data_file.save()
                    
                except Exception as e:
                    # En cas d'erreur, supprimer le fichier et l'enregistrement
                    data_file.file.delete(save=False)
                    data_file.delete()
                    raise Exception(f"Erreur lors de l'analyse du fichier : {str(e)}")

                
                messages.success(request, 'Fichier uploadé avec succès!')
                return redirect('file_list')
                
            except Exception as e:
                messages.error(request, f'Erreur lors de l\'upload: {str(e)}')
                return redirect('upload_file')
    else:
        form = DataFileUploadForm()
    
    return render(request, 'data_processor/upload.html', {
        'form': form
    })


@login_required
def preview_file(request, pk):
    try:
        data_file = DataFile.objects.get(pk=pk)
        # Charger les données
        if data_file.file_type == 'csv':
            df = pd.read_csv(data_file.file.path)
        else:
            df = pd.read_json(data_file.file.path)
        
        # Limiter à 100 premières lignes pour la prévisualisation
        preview_data = df.head(100)
        
        # Convertir en HTML avec des classes Bootstrap
        table_html = preview_data.to_html(
            classes=['table', 'table-striped', 'table-hover'],
            index=False,
            na_rep='N/A'
        )
        
        return render(request, 'data_processor/preview.html', {
            'data_file': data_file,
            'table_html': table_html,
            'row_count': len(df),
            'column_count': len(df.columns)
        })
        
    except Exception as e:
        messages.error(request, f'Erreur lors de la prévisualisation: {str(e)}')
        return redirect('file_list')


@login_required
def export_file(request, pk):
    try:
        data_file = DataFile.objects.get(pk=pk)
        export_format = request.GET.get('format', 'csv')
        
        # Vérifier si le fichier a été traité
        if not data_file.processed:
            messages.error(request, 'Le fichier doit être traité avant l\'exportation.')
            return redirect('file_list')
        
        # Charger les données traitées
        processed_path = f'{data_file.file.path}_processed'
        if data_file.file_type == 'csv':
            df = pd.read_csv(processed_path)
        else:
            df = pd.read_json(processed_path)
        
        # Préparer le nom du fichier exporté
        filename_base = os.path.splitext(data_file.original_filename)[0]
        
        # Exporter selon le format demandé
        if export_format == 'excel':
            response = HttpResponse(content_type='application/vnd.ms-excel')
            response['Content-Disposition'] = f'attachment; filename="{filename_base}_processed.xlsx"'
            df.to_excel(response, index=False)
        elif export_format == 'json':
            response = HttpResponse(content_type='application/json')
            response['Content-Disposition'] = f'attachment; filename="{filename_base}_processed.json"'
            df.to_json(response, orient='records')
        else:  # csv par défaut
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{filename_base}_processed.csv"'
            df.to_csv(response, index=False)
        
        return response
        
    except Exception as e:
        messages.error(request, f'Erreur lors de l\'exportation: {str(e)}')
        return redirect('file_list')


@login_required
def delete_file(request, pk):
    try:
        data_file = DataFile.objects.get(pk=pk)
        # Supprimer le fichier physique
        if os.path.exists(data_file.file.path):
            os.remove(data_file.file.path)
            
        # Supprimer le fichier traité s'il existe
        processed_path = f'{data_file.file.path}_processed'
        if os.path.exists(processed_path):
            os.remove(processed_path)
            
        # Supprimer l'enregistrement de la base de données
        data_file.delete()
        
        messages.success(request, 'Fichier supprimé avec succès!')
    except Exception as e:
        messages.error(request, f'Erreur lors de la suppression: {str(e)}')
    
    return redirect('file_list')


def transform_to_csv(request, pk):
    data_file = DataFile.objects.get(pk=pk)
    try:
        if data_file.file_type != 'xml':
            messages.error(request, 'Cette fonction est uniquement disponible pour les fichiers XML.')
            return redirect('file_list')

        # Charger les données XML
        from app.utils.xml_processor import load_xml_data
        df = load_xml_data(data_file.file.path)
        if df is None:
            raise ValueError("Erreur lors du chargement du fichier XML")

        # Créer un nouveau nom de fichier pour le CSV
        filename_base = os.path.splitext(data_file.original_filename)[0]
        csv_filename = f"{filename_base}.csv"

        # Préparer la réponse HTTP
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{csv_filename}"'

        # Convertir et sauvegarder en CSV
        df.to_csv(response, index=False)

        return response

    except Exception as e:
        messages.error(request, f'Erreur lors de la transformation en CSV: {str(e)}')
        return redirect('file_list')
