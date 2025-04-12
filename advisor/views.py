from django.shortcuts import render, redirect
from .models import UserProfile, JobMarketData, CareerAdviceHistory, QuizQuestion, QuizAnswer
from .gemini import get_career_advice, generate_quiz_question
from .forms import ResumeForm
from .utils import get_resume_feedback
import markdown
from django.utils.html import mark_safe
from .gemini import get_career_advice
from .github_utils import find_similar_github_users

MAX_QUIZ_QUESTIONS = 3

def home(request):
    return render(request, 'advisor/home.html')

def dashboard(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        skills = request.POST.get('skills')
        experience = int(request.POST.get('experience'))

        request.session['user_email'] = email
        request.session['user_name'] = name

        profile, created = UserProfile.objects.get_or_create(email=email)
        profile.name = name
        profile.skills = skills
        profile.experience = experience
        profile.save()

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

        raw_ai = get_career_advice(name, skills, experience)
        ai_response = markdown.markdown(raw_ai)

        CareerAdviceHistory.objects.create(
            name=name,
            email=email,
            skills=skills,
            experience=experience,
            advice=ai_response
        )

        return redirect('dynamic_quiz')

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

def dynamic_quiz(request):
    email = request.session.get('user_email')
    name = request.session.get('user_name')

    if not email or not name:
        return redirect('home')

    questions = QuizQuestion.objects.filter(user_email=email).order_by('timestamp')
    
    if request.method == 'POST':
        for key in request.POST:
            if key.startswith('answer_'):
                question_id = key.split('_')[1]
                answer_text = request.POST.get(key)
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
        
        # Check if we have all answers
        answered_questions = QuizAnswer.objects.filter(user_email=email).count()
        if answered_questions >= MAX_QUIZ_QUESTIONS:
            return redirect('final_dashboard')
        else:
            # If not all questions are answered, stay on quiz page
            return redirect('dynamic_quiz')

    # Get previous Q&As for context
    previous_qas = []
    for q in questions:
        try:
            answer = QuizAnswer.objects.filter(
                question=q,
                user_email=email
            ).order_by('-timestamp').first()
            
            if answer:
                previous_qas.append({
                    'question': q.question_text,
                    'answer': answer.answer_text
                })
        except QuizAnswer.DoesNotExist:
            continue

    # Generate new questions until we have 3
    while questions.count() < MAX_QUIZ_QUESTIONS:
        # Format previous Q&As for the prompt
        qa_context = "\n".join([
            f"Q: {qa['question']}\nA: {qa['answer']}"
            for qa in previous_qas
        ])
        
        # Get user profile data if available
        try:
            profile = UserProfile.objects.get(email=email)
            skills = profile.skills
            experience = profile.experience
        except UserProfile.DoesNotExist:
            skills = ""
            experience = 0

        # Generate new question using Gemini
        new_question = generate_quiz_question(
            name=name,
            skills=skills,
            experience=experience,
            previous_qas=qa_context
        )
        
        QuizQuestion.objects.create(
            user_email=email,
            question_text=new_question
        )
        
        # Refresh questions queryset
        questions = QuizQuestion.objects.filter(user_email=email).order_by('timestamp')[:MAX_QUIZ_QUESTIONS]

    return render(request, 'advisor/dynamic_quiz.html', {'questions': questions})

def get_similar_users(current_user):
    current_skills = set(skill.strip().lower() for skill in current_user.skills.split(","))
    experience = current_user.experience

    other_users = UserProfile.objects.exclude(email=current_user.email)
    matches = []

    for user in other_users:
        user_skills = set(skill.strip().lower() for skill in user.skills.split(","))
        skill_overlap = current_skills & user_skills
        if len(skill_overlap) >= 2 and abs(user.experience - experience) <= 1:
            matches.append({
                'name': user.name,
                'skills': ", ".join(user_skills),
                'experience': user.experience,
                'common_skills': ", ".join(skill_overlap)
            })

    return matches

def final_dashboard(request):
    email = request.session.get('user_email')
    name = request.session.get('user_name')

    if not email or not name:
        return redirect('home')

    profile = UserProfile.objects.get(email=email)
    skills = profile.skills
    experience = profile.experience

    answers = QuizAnswer.objects.filter(user_email=email).select_related('question')
    answer_data = "\n".join([f"Q: {a.question.question_text}\nA: {a.answer_text}" for a in answers])

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

    prompt_context = f"{name} has {experience} years experience with skills {skills}. " \
                     f"Here are more details from their quiz:\n{answer_data}"

    raw_advice = get_career_advice(name, skills, experience)
    advice = mark_safe(markdown.markdown(raw_advice))

    similar_people = get_similar_users(profile)
    
    # Get GitHub matches based on user skills
    github_matches = find_similar_github_users([s.strip().lower() for s in skills.split(",")])

    context = {
        'name': name,
        'skills': skills,
        'experience': experience,
        'recommendations': recommendations,
        'career_advice': advice,
        'quiz_data': [{'question': a.question.question_text, 'answer': a.answer_text} for a in answers],
        'similar_people': similar_people,
        'github_people': github_matches,
    }
    return render(request, 'advisor/final_dashboard.html', context)

def people_like_you(request):
    email = request.session.get('user_email')
    profile = UserProfile.objects.get(email=email)

    skills = [s.strip().lower() for s in profile.skills.split(",")]

    github_people = find_similar_github_users(skills)

    return render(request, 'advisor/people_like_you.html', {
        'github_people': github_people,
        'user_profile': profile
    })