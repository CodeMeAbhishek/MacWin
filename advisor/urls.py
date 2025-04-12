# advisor/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('resume-tips/', views.resume_tips, name='resume_tips'),
    path('history/', views.advice_history, name='advice_history'),
    path('quiz/', views.dynamic_quiz, name='dynamic_quiz'),
    path('final-dashboard/', views.final_dashboard, name='final_dashboard'),
    path('start-quiz/', views.start_quiz, name='start_quiz'),
    path('quiz-questions/<int:user_id>/', views.quiz_questions, name='quiz_questions'),
    path('people-like-you/', views.people_like_you, name='people_like_you'),
]