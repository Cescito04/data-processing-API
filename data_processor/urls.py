from django.urls import path
from . import views

urlpatterns = [
    path('', views.FileListView.as_view(), name='file_list'),
    path('upload/', views.upload_file, name='upload_file'),
    path('process/<int:pk>/', views.process_file, name='process_file'),
    path('preview/<int:pk>/', views.preview_file, name='preview_file'),
    path('export/<int:pk>/', views.export_file, name='export_file'),
    path('delete/<int:pk>/', views.delete_file, name='delete_file'),
]