"""
URL configuration for the screening app.
"""
from django.urls import path
from . import views

app_name = 'screening'

urlpatterns = [
    path('', views.form_view, name='form'),
    path('predict/', views.predict_view, name='predict'),
    path('bulk-upload/', views.bulk_upload_view, name='bulk_upload'),
    path('resume-upload/', views.resume_upload_view, name='resume_upload'),
]
