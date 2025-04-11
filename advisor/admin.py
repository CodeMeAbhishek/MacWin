from django.contrib import admin
from .models import UserProfile, JobMarketData

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'skills', 'experience')

@admin.register(JobMarketData)
class JobMarketDataAdmin(admin.ModelAdmin):
    list_display = ('role', 'required_skills', 'average_salary', 'demand_level')
