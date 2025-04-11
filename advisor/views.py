from django.shortcuts import render
from .models import UserProfile

# Create your views here.

def home(request):
    return render(request, 'advisor/home.html')

def dashboard(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        skills = request.POST.get('skills')
        experience = request.POST.get('experience')

        profile, created = UserProfile.objects.get_or_create(email=email)
        profile.name = name
        profile.skills = skills
        profile.experience = experience
        profile.save()

        context = {
            'name': name,
            'skills': skills,
            'experience': experience
        }
        return render(request, 'advisor/dashboard.html', context)
    return render(request, 'advisor/home.html')