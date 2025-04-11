# advisor/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('resume-tips/', views.resume_tips, name='resume_tips'),
    path('history/', views.advice_history, name='advice_history'),
]