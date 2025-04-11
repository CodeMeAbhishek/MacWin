from django.db import models

# Create your models here.
class UserProfile(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    skills = models.TextField()  # comma-separated
    experience = models.PositiveIntegerField(default=0)  # years

class JobMarketData(models.Model):
    role = models.CharField(max_length=100)
    required_skills = models.TextField()
    average_salary = models.PositiveIntegerField()
    demand_level = models.CharField(max_length=50)