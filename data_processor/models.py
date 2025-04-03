from django.db import models
from django.utils import timezone

class DataFile(models.Model):
    file = models.FileField(upload_to='uploads/%Y/%m/%d/', verbose_name='Fichier')
    original_filename = models.CharField(max_length=255, verbose_name='Nom du fichier original')
    upload_date = models.DateTimeField(default=timezone.now, verbose_name='Date d\'importation')
    file_type = models.CharField(max_length=10, verbose_name='Type de fichier')
    processed = models.BooleanField(default=False, verbose_name='Traité')
    row_count = models.IntegerField(default=0, verbose_name='Nombre de lignes')
    column_count = models.IntegerField(default=0, verbose_name='Nombre de colonnes')
    missing_values = models.JSONField(default=dict, verbose_name='Valeurs manquantes')
    outliers = models.JSONField(default=dict, verbose_name='Valeurs aberrantes')
    processing_summary = models.JSONField(default=dict, verbose_name='Résumé du traitement')

    class Meta:
        verbose_name = 'Fichier de données'
        verbose_name_plural = 'Fichiers de données'
        ordering = ['-upload_date']

    def __str__(self):
        return f"{self.original_filename} (importé le {self.upload_date.strftime('%d/%m/%Y')})"
