from django.shortcuts import render, redirect, get_object_or_404
from .models import UserProfile, JobMarketData, CareerAdviceHistory, QuizQuestion, QuizAnswer
from .gemini import (
    get_career_advice,
    generate_quiz_question,
    generate_dynamic_quiz,
    get_ai_dashboard_insights
)
from .forms import ResumeForm
from .utils import get_resume_feedback
import markdown
from django.utils.html import mark_safe
from .github_utils import find_similar_github_users
import json
import asyncio
from scraper.views import JobScraper
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
import traceback
import re

MAX_QUIZ_QUESTIONS = 3

def get_theme_class(request):
    theme = request.session.get('theme', 'light')
    return 'dark-mode' if theme == 'dark' else ''

@require_http_methods(["POST"])
def set_theme(request):
    data = json.loads(request.body)
    theme = data.get('theme', 'light')
    request.session['theme'] = theme
    return JsonResponse({'status': 'success'})

@ensure_csrf_cookie
def landing(request):
    theme_class = get_theme_class(request)
    return render(request, 'advisor/landing.html', {'theme_class': theme_class})

@ensure_csrf_cookie
def home(request):
    theme_class = get_theme_class(request)
    return render(request, 'advisor/home.html', {'theme_class': theme_class})

def dashboard(request):
    print("\n=== Dashboard View ===")
    print(f"Request method: {request.method}")
    print(f"POST data: {request.POST}")
    
    if request.method == "POST":
        print("\nProcessing POST request...")
        
        # Get form data
        form_data = {
            'name': request.POST.get('name', '').strip(),
            'email': request.POST.get('email', '').strip(),
            'skills': request.POST.get('skills', '').strip(),
            'years_of_experience': request.POST.get('years_of_experience', ''),
            'role': request.POST.get('role', ''),
            'age': request.POST.get('age', '')
        }
        
        print(f"\nForm data received: {form_data}")

        # Validate required fields
        missing_fields = [field for field, value in form_data.items() if not value]
        if missing_fields:
            print(f"\nMissing required fields: {missing_fields}")
            return render(request, 'advisor/home.html', {
                'error': f'Please fill in all required fields: {", ".join(missing_fields)}',
                'form_data': form_data
            })

        try:
            # Convert numeric fields
            years_of_experience = int(form_data['years_of_experience'])
            age = int(form_data['age'])
            
            print(f"\nValidated numeric fields - Experience: {years_of_experience}, Age: {age}")
            
            # Additional validation
            if years_of_experience < 0 or years_of_experience > 50:
                raise ValueError("Years of experience must be between 0 and 50")
            if age < 15 or age > 100:
                raise ValueError("Age must be between 15 and 100")
                
        except ValueError as e:
            print(f"\nValidation error: {str(e)}")
            return render(request, 'advisor/home.html', {
                'error': f'Invalid input: {str(e)}',
                'form_data': form_data
            })

        try:
            print("\nSaving to session and database...")
            # Save to session
            request.session['user_email'] = form_data['email']
            request.session['user_name'] = form_data['name']

            # Create or update user profile
            profile, created = UserProfile.objects.get_or_create(
                email=form_data['email'],
                defaults={
                    'name': form_data['name'],
                    'skills': form_data['skills'],
                    'years_of_experience': years_of_experience,
                    'role': form_data['role'],
                    'age': age
                }
            )
            
            if not created:
                # Update existing profile
                profile.name = form_data['name']
                profile.skills = form_data['skills']
                profile.years_of_experience = years_of_experience
                profile.role = form_data['role']
                profile.age = age
                profile.save()

            print(f"\nUser profile {'created' if created else 'updated'}: {profile.id}")
            
            # Clear any existing quiz data
            QuizQuestion.objects.filter(user_email=form_data['email']).delete()
            QuizAnswer.objects.filter(user_email=form_data['email']).delete()
            
            print("\nRedirecting to dynamic_quiz...")
            return redirect('dynamic_quiz')

        except Exception as e:
            print(f"\nError saving profile: {str(e)}")
            import traceback
            traceback.print_exc()
            return render(request, 'advisor/home.html', {
                'error': 'An error occurred while saving your profile. Please try again.',
                'form_data': form_data
            })

    return render(request, 'advisor/home.html')

def resume_tips(request):
    theme_class = get_theme_class(request)
    feedback = None
    if request.method == 'POST':
        form = ResumeForm(request.POST)
        if form.is_valid():
            resume_text = form.cleaned_data['resume_text']
            feedback = get_resume_feedback(resume_text)
    else:
        form = ResumeForm()
    return render(request, 'advisor/resume_tips.html', {
        'form': form, 
        'feedback': feedback,
        'theme_class': theme_class
    })

def advice_history(request):
    theme_class = get_theme_class(request)
    email = request.GET.get('email') or request.session.get('user_email')
    history = []

    if email:
        history = CareerAdviceHistory.objects.filter(email=email).order_by('-timestamp')

    return render(request, 'advisor/advice_history.html', {
        'history': history,
        'theme_class': theme_class
    })

def format_ai_insights(raw_insights):
    """Format the AI insights into styled HTML sections"""
    # First, clean up the text and handle markdown-style formatting
    formatted_html = []
    
    # Split into sections
    sections = raw_insights.split('\n')
    
    in_list = False
    in_path_section = False
    
    for line in sections:
        line = line.strip()
        if not line:
            if in_list:
                formatted_html.append('</ul>')
                in_list = False
            continue
            
        # Handle main title
        if line.startswith('**Career Development Plan for'):
            formatted_html.append(f'<div class="main-title-section"><h1>{line.strip("*")}</h1></div>')
            continue
            
        # Handle major section headers
        if line.startswith('**1. Career Path Analysis'):
            formatted_html.append('<div class="major-section-header"><h2>Career Path Analysis</h2>')
            formatted_html.append('<div class="section-description">')
            continue
            
        # Handle career path description
        if line.startswith('Based on') and 'skills' in line and 'career paths' in line:
            formatted_html.append(f'<p>{line}</p></div></div>')
            continue
            
        # Handle path sections
        if line.startswith('* **Path'):
            if in_path_section:
                formatted_html.append('</div>')
            in_path_section = True
            path_title = line.replace('* **', '').replace(':**', ':')
            formatted_html.append(f'<div class="path-section"><div class="path-title">{path_title}</div>')
            continue
            
        # Handle suitability sections
        if line.startswith('* **Suitability:**'):
            suitability_text = line.replace('* **Suitability:**', '').strip()
            formatted_html.append(f'<div class="suitability"><strong>Suitability:</strong> {suitability_text}</div>')
            continue
            
        # Handle explanation sections
        if line.startswith('* **Explanation:**'):
            explanation_text = line.replace('* **Explanation:**', '').strip()
            formatted_html.append(f'<div class="explanation"><strong>Explanation:</strong> {explanation_text}</div>')
            continue
            
        # Handle required skills section
        if line.startswith('* **Required Skills'):
            formatted_html.append('<div class="required-skills"><strong>Required Skills:</strong>')
            formatted_html.append('<div class="skills-required">')
            continue
            
        # Handle skill items
        if line.startswith('* ') and 'Required Skills' in formatted_html[-2]:
            skill = line.replace('* ', '').strip()
            if '*' in skill:  # Check if skill has a note
                skill_parts = skill.split('*')
                skill_name = skill_parts[0].strip()
                skill_note = f' <span class="skill-note">({skill_parts[1].strip("()")})</span>'
                formatted_html.append(f'<span class="skill-tag">{skill_name}{skill_note}</span>')
            else:
                formatted_html.append(f'<span class="skill-tag">{skill}</span>')
            continue
            
        # Handle regular list items
        if line.startswith('* '):
            if not in_list:
                formatted_html.append('<ul>')
                in_list = True
            list_item = line.replace('* ', '')
            # Remove markdown formatting from list items
            list_item = list_item.replace('**', '')
            formatted_html.append(f'<li>{list_item}</li>')
            continue
            
        # Handle regular paragraphs
        if in_list:
            formatted_html.append('</ul>')
            in_list = False
        line = line.replace('**', '')  # Remove any remaining markdown
        formatted_html.append(f'<p>{line}</p>')
    
    # Close any open sections
    if in_path_section:
        formatted_html.append('</div>')
    if in_list:
        formatted_html.append('</ul>')
    
    return '\n'.join(formatted_html)

def dynamic_quiz(request):
    theme_class = get_theme_class(request)
    email = request.session.get('user_email')
    name = request.session.get('user_name')

    if not email or not name:
        return redirect('home')

    try:
        user = UserProfile.objects.get(email=email)
    except UserProfile.DoesNotExist:
        return redirect('home')
    
    if request.method == 'POST':
        answers = []
        for key, value in request.POST.items():
            if key.startswith('answer_'):
                question_id = key.split('_')[1]
                answer_text = value.strip()
                if answer_text:  # Only process non-empty answers
                    question = QuizQuestion.objects.get(id=question_id)
                    # Delete any existing answers for this question and user
                    QuizAnswer.objects.filter(
                        user_email=email,
                        question=question
                    ).delete()
                    # Create new answer
                    QuizAnswer.objects.create(
                        user_email=email,
                        question=question,
                        answer_text=answer_text
                    )
                    answers.append(answer_text)
        
        # Store answers in user profile
        user.quiz_answers = json.dumps(answers)
        user.save()
        
        # Generate AI insights based on answers
        ai_insights = get_ai_dashboard_insights(user, answers)
        
        # Format the insights before storing
        formatted_insights = format_ai_insights(ai_insights)
        
        # Store insights in session for dashboard
        request.session['ai_insights'] = formatted_insights
        
        # Store in CareerAdviceHistory
        CareerAdviceHistory.objects.create(
            name=user.name,
            email=user.email,
            skills=user.skills,
            experience=user.years_of_experience,
            advice=formatted_insights
        )
        
        return redirect('final_dashboard')

    # For GET request, generate and show the quiz
    # Clear any existing questions for this user
    QuizQuestion.objects.filter(user_email=email).delete()
    
    # Generate new questions
    questions = generate_dynamic_quiz(user)
    
    # Create QuizQuestion objects for each question
    quiz_questions = []
    for question_text in questions:
        question = QuizQuestion.objects.create(
            user_email=email,
            question_text=question_text,
            for_students=(user.role == 'Student'),
            for_teachers=(user.role == 'Teacher'),
            for_job_seekers=(user.role == 'Job-seeker'),
            for_general=(user.role == 'Individual')
        )
        quiz_questions.append(question)
    
    print(f"Generated {len(quiz_questions)} questions for {email}")  # Debug log
    
    return render(request, 'advisor/dynamic_quiz.html', {
        'questions': quiz_questions,
        'theme_class': theme_class
    })

def get_similar_users(current_user):
    current_skills = set(skill.strip().lower() for skill in current_user.skills.split(","))
    experience = current_user.years_of_experience

    other_users = UserProfile.objects.exclude(email=current_user.email)
    matches = []

    for user in other_users:
        user_skills = set(skill.strip().lower() for skill in user.skills.split(","))
        mutual_skills = current_skills & user_skills

        if len(mutual_skills) >= 1 and abs(user.years_of_experience - experience) <= 2:
            matches.append({
                'name': user.name,
                'skills': ", ".join(user_skills),
                'experience': user.years_of_experience,
                'common_skills': list(mutual_skills),  # 🔥 Mutual skills to display
            })

    return matches

def final_dashboard(request):
    theme_class = get_theme_class(request)
    email = request.session.get('user_email')
    name = request.session.get('user_name')

    if not email or not name:
        return redirect('home')

    try:
        profile = UserProfile.objects.get(email=email)
    except UserProfile.DoesNotExist:
        return redirect('home')

    skills = profile.skills
    years_of_experience = profile.years_of_experience

    # Get quiz answers
    answers = QuizAnswer.objects.filter(user_email=email).select_related('question')
    answer_data = "\n".join([f"Q: {a.question.question_text}\nA: {a.answer_text}" for a in answers])

    # Get job recommendations
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

    recommendations = sorted(recommendations, key=lambda x: (-x['match_score'], -x['average_salary']))

    # Get AI insights
    ai_insights = request.session.get('ai_insights')
    if not ai_insights:
        # Generate new insights if not in session
        raw_insights = get_ai_dashboard_insights(profile, [a.answer_text for a in answers])
        ai_insights = format_ai_insights(raw_insights)
        request.session['ai_insights'] = ai_insights

    # Get similar users and GitHub matches
    similar_people = get_similar_users(profile)
    github_matches = find_similar_github_users([s.strip().lower() for s in skills.split(",")])

    # 🔄 Real-Time LinkedIn Job Listings
    realtime_jobs = []
    try:
        scraper = JobScraper()
        # Convert set of skills back to comma-separated string
        skills_string = ",".join(user_skills)
        print(f"Searching jobs for skills: {skills_string}")  # Debug print
        realtime_jobs = asyncio.run(scraper.scrape_multiple_technologies(
            skills_string,
            session_id=email
        ))
        print(f"Found {len(realtime_jobs)} jobs")  # Debug print
    except Exception as e:
        print("⚠️ Real-time scraping failed:", str(e))
        traceback.print_exc()  # Add full traceback

    context = {
        'user': profile,
        'skills': skills.split(','),
        'experience': years_of_experience,
        'recommendations': recommendations,
        'ai_insights': mark_safe(ai_insights),
        'quiz_data': [{'question': a.question.question_text, 'answer': a.answer_text} for a in answers],
        'similar_people': similar_people,
        'github_people': github_matches,
        'realtime_jobs': realtime_jobs,
        'theme_class': theme_class
    }

    return render(request, 'advisor/final_dashboard.html', context)

def people_like_you(request):
    theme_class = get_theme_class(request)
    email = request.session.get('user_email')
    profile = UserProfile.objects.get(email=email)

    skills = [s.strip().lower() for s in profile.skills.split(",")]

    github_people = find_similar_github_users(skills)

    return render(request, 'advisor/people_like_you.html', {
        'github_people': github_people,
        'user_profile': profile,
        'theme_class': theme_class
    })

def start_quiz(request):
    theme_class = get_theme_class(request)
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        skills = request.POST.get('skills')
        years_of_experience = request.POST.get('years_of_experience')
        age = request.POST.get('age')
        role = request.POST.get('role')

        user, created = UserProfile.objects.update_or_create(
            email=email,
            defaults={
                'name': name,
                'skills': skills,
                'years_of_experience': years_of_experience,
                'age': age,
                'role': role,
            }
        )

        # Redirect to dynamic quiz generation
        return redirect('quiz', user_id=user.id)

    return render(request, 'advisor/start_quiz.html', {
        'theme_class': theme_class
    })

def quiz_questions(request, user_id):
    theme_class = get_theme_class(request)
    profile = get_object_or_404(UserProfile, id=user_id)
    
    # Generate dynamic questions based on user profile
    questions = generate_dynamic_quiz(profile)
    
    # Create QuizQuestion objects for each question
    quiz_questions = []
    for question_text in questions:
        question = QuizQuestion.objects.create(
            user_email=profile.email,
            question_text=question_text,
            for_students=(profile.role == 'Student'),
            for_teachers=(profile.role == 'Teacher'),
            for_job_seekers=(profile.role == 'Job-seeker'),
            for_general=(profile.role == 'Individual')
        )
        quiz_questions.append(question)
    
    return render(request, 'advisor/quiz_questions.html', {
        'user': profile,
        'questions': quiz_questions,
        'theme_class': theme_class
    })

def get_ai_insights(request):
    email = request.session.get('user_email')
    if not email:
        return JsonResponse({'error': 'Please complete the quiz first'}, status=401)
    
    try:
        profile = UserProfile.objects.get(email=email)
        answers = QuizAnswer.objects.filter(user_email=email).select_related('question')
        answer_texts = [a.answer_text for a in answers]
        
        # Generate AI insights
        raw_insights = get_ai_dashboard_insights(profile, answer_texts)
        formatted_insights = format_ai_insights(raw_insights)
        
        return JsonResponse({
            'insights': mark_safe(formatted_insights)
        })
    except UserProfile.DoesNotExist:
        return JsonResponse({'error': 'User profile not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)