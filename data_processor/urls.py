from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('', login_required(views.FileListView.as_view()), name='file_list'),
    path('upload/', views.upload_file, name='upload_file'),
    path('process/<int:pk>/', views.process_file, name='process_file'),
    path('preview/<int:pk>/', views.preview_file, name='preview_file'),
    path('export/<int:pk>/', views.export_file, name='export_file'),
    path('delete/<int:pk>/', views.delete_file, name='delete_file'),
    path('clear/', views.clear_all_files, name='clear_all_files'),
]