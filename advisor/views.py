from django.shortcuts import render
from .models import UserProfile, JobMarketData, CareerAdviceHistory
from .gemini import get_career_advice
from .forms import ResumeForm
from .utils import get_resume_feedback
import markdown

def home(request):
    return render(request, 'advisor/home.html')

def dashboard(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        skills = request.POST.get('skills')
        experience = int(request.POST.get('experience'))

        # Save email and name in session
        request.session['user_email'] = email
        request.session['user_name'] = name

        # Save or update user profile
        profile, created = UserProfile.objects.get_or_create(email=email)
        profile.name = name
        profile.skills = skills
        profile.experience = experience
        profile.save()

        # Match jobs
        user_skills = set(skill.strip().lower() for skill in skills.split(","))
        jobs = JobMarketData.objects.all()
        recommendations = []

        for job in jobs:
            job_skills = set(skill.strip().lower() for skill in job.required_skills.split(","))
            match_score = len(user_skills & job_skills)
            if match_score > 0:
                recommendations.append({
                    'role': job.role,
                    'match_score': match_score,
                    'required_skills': job.required_skills,
                    'average_salary': job.average_salary,
                    'demand_level': job.demand_level
                })

        # Sort by match & salary
        recommendations = sorted(recommendations, key=lambda x: (-x['match_score'], -x['average_salary']))

        # Get AI advice and store it
        raw_ai = get_career_advice(name, skills, experience)
        ai_response = markdown.markdown(raw_ai)

        CareerAdviceHistory.objects.create(
            name=name,
            email=email,
            skills=skills,
            experience=experience,
            advice=ai_response
        )

        context = {
            'name': name,
            'skills': skills,
            'experience': experience,
            'recommendations': recommendations,
            'ai_response': ai_response,
        }
        return render(request, 'advisor/dashboard.html', context)

    return render(request, 'advisor/home.html')

def resume_tips(request):
    feedback = None
    if request.method == 'POST':
        form = ResumeForm(request.POST)
        if form.is_valid():
            resume_text = form.cleaned_data['resume_text']
            feedback = get_resume_feedback(resume_text)
    else:
        form = ResumeForm()
    return render(request, 'advisor/resume_tips.html', {'form': form, 'feedback': feedback})

def advice_history(request):
    email = request.GET.get('email') or request.session.get('user_email')
    history = []

    if email:
        history = CareerAdviceHistory.objects.filter(email=email).order_by('-timestamp')

    return render(request, 'advisor/advice_history.html', {'history': history})
