from django.shortcuts import render, redirect
from django.views.generic import ListView
from django.contrib import messages
from django.http import JsonResponse, FileResponse, HttpResponse
from .models import DataFile
from .forms import DataFileUploadForm, DataProcessingForm
import pandas as pd
import numpy as np
import os

def process_file(request, pk):
    data_file = DataFile.objects.get(pk=pk)
    
    if request.method == 'POST':
        form = DataProcessingForm(request.POST)
        if form.is_valid():
            try:
                # Chargement des données
                if data_file.file_type == 'csv':
                    df = pd.read_csv(data_file.file.path)
                else:
                    df = pd.read_json(data_file.file.path)
                
                # Récupérer la colonne cible si spécifiée
                target_column = form.cleaned_data.get('target_column')
                if target_column and target_column in df.columns:
                    target_data = df[target_column]
                    df_features = df.drop(columns=[target_column])
                else:
                    target_data = None
                    df_features = df
                
                processing_summary = {}
                
                # Traitement des valeurs manquantes
                if form.cleaned_data['handle_missing']:
                    for column in df_features.columns:
                        # Identifier le type de colonne
                        is_binary = df_features[column].dropna().isin([0, 1]).all()
                        is_numeric = pd.api.types.is_numeric_dtype(df_features[column])
                        
                        strategy = form.cleaned_data['missing_strategy']
                        
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
                if form.cleaned_data['handle_outliers']:
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
                if form.cleaned_data['normalize_data']:
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
                if form.cleaned_data['remove_duplicates']:
                    initial_rows = len(df_features)
                    df_features = df_features.drop_duplicates()
                    processing_summary['duplicates'] = f'{initial_rows - len(df_features)} doublons supprimés'
                
                # Réintégrer la colonne cible si elle existe
                if target_data is not None:
                    df_processed = pd.concat([df_features, target_data], axis=1)
                else:
                    df_processed = df_features
                
                # Sauvegarde du fichier traité
                processed_path = f'{data_file.file.path}_processed'
                if data_file.file_type == 'csv':
                    df_processed.to_csv(processed_path, index=False)
                else:
                    df_processed.to_json(processed_path)
                
                data_file.processed = True
                data_file.processing_summary = processing_summary
                data_file.save()
                
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


class FileListView(ListView):
    model = DataFile
    template_name = 'data_processor/file_list.html'
    context_object_name = 'files'
    ordering = ['-upload_date']


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


def preview_file(request, pk):
    data_file = DataFile.objects.get(pk=pk)
    try:
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


def export_file(request, pk):
    data_file = DataFile.objects.get(pk=pk)
    export_format = request.GET.get('format', 'csv')
    
    try:
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


def delete_file(request, pk):
    data_file = DataFile.objects.get(pk=pk)
    try:
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
