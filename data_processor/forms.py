from django import forms
from .models import DataFile

class DataFileUploadForm(forms.ModelForm):
    class Meta:
        model = DataFile
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.csv,.json,.xml'
            })
        }

class DataProcessingForm(forms.Form):
    # Nouveau champ pour la variable cible
    target_column = forms.CharField(
        label='Colonne cible (optionnelle)',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom de la colonne à exclure du traitement'
        }),
        help_text="Laissez vide si aucune colonne cible"
    )
    
    # Section: Traitement des valeurs manquantes
    handle_missing = forms.BooleanField(
        label='Traiter les valeurs manquantes',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    missing_strategy = forms.ChoiceField(
        label='Méthode de traitement',
        choices=[
            ('mean', 'Moyenne (numérique seulement)'),
            ('median', 'Médiane (numérique seulement)'),
            ('mode', 'Mode (tous types)'),
            ('drop', 'Supprimer les lignes')
        ],
        initial='mode',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Section: Traitement des outliers
    handle_outliers = forms.BooleanField(
        label='Traiter les valeurs aberrantes',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    outliers_method = forms.ChoiceField(
        label='Méthode de traitement',
        choices=[
            ('iqr', 'Méthode IQR (recommandé)'),
            ('zscore', 'Score Z (σ=3)')
        ],
        initial='iqr',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Section: Normalisation
    normalize_data = forms.BooleanField(
        label='Normaliser les données',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    normalization_method = forms.ChoiceField(
        label='Méthode de normalisation',
        choices=[
            ('minmax', 'Min-Max [0, 1] (conserve les proportions)'),
            ('standard', 'Standard (moyenne=0, σ=1)'),
            ('robust', 'Robuste (médiane=0, IQR=1)')
        ],
        initial='minmax',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Section: Doublons
    remove_duplicates = forms.BooleanField(
        label='Supprimer les doublons',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    # Section: Types de données
    preserve_dtypes = forms.BooleanField(
        label='Conserver les types de données originaux',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Empêche la conversion non désirée en float"
    )

    def __init__(self, *args, **kwargs):
        columns = kwargs.pop('columns', [])
        super().__init__(*args, **kwargs)
        
        # Mise à jour dynamique des choix pour la colonne cible
        if columns:
            self.fields['target_column'].widget = forms.Select(
                choices=[('', '--- Aucune ---')] + [(col, col) for col in columns],
                attrs={'class': 'form-select'}
            )