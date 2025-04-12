import markdown
from .gemini import generate_gemini_response
import re

def get_resume_feedback(resume_text):
    prompt = f"""
You are a highly experienced career advisor. Carefully review the following resume content.

1. Give 5 improvement suggestions in bullet points.
2. Then, provide 3 smart interview tips tailored to this resume.

Resume:
\"\"\"
{resume_text}
\"\"\"
"""
    raw_response = generate_gemini_response(prompt)
    html_response = markdown.markdown(raw_response)
    return html_response

def generate_dynamic_questions(name, skills, experience):
    # ...
    print("Prompt to Gemini:\n", prompt)
    print("Raw Gemini Response:\n", response)

    questions = re.findall(r'\d+\.\s+(.*?)(?=\n\d+\.|\Z)', response.strip())
    print("Parsed Questions:\n", questions)
    return questions

def generate_dynamic_quiz(user):
    skills = [s.strip().lower() for s in user.skills.split(',')]
    role = user.role.lower()
    age = user.age or 0
    experience = user.years_of_experience

    base_questions = []

    # 🎓 Role-specific
    if role == 'student':
        base_questions += [
            f"What tech projects have you enjoyed building in college with your skills in {', '.join(skills)}?",
            "Do you prefer internships or building real-world apps on your own?"
        ]
    elif role == 'job-seeker':
        base_questions += [
            f"What kind of jobs are you targeting with your experience in {', '.join(skills)}?",
            "Have you prepared for coding interviews or system design interviews?"
        ]
    elif role == 'teacher':
        base_questions += [
            "What topics do you enjoy teaching the most?",
            "Do you create educational content or tutorials?"
        ]
    elif role == 'individual':
        base_questions += [
            f"What motivates you to upskill in {', '.join(skills)}?",
            "Do you aim to freelance, contribute to open source, or something else?"
        ]

    # 👶 Age-based adjustments
    if age < 18:
        base_questions.append("Are you exploring tech out of curiosity or with a career goal in mind?")
    elif age > 35:
        base_questions.append("Are you looking to switch careers or deepen your existing expertise?")

    # 💼 Experience-based customization
    if experience < 2:
        base_questions.append("Are you looking for mentorship or guided learning paths?")
    elif experience > 5:
        base_questions.append("Have you led any teams or handled complex technical decisions?")

    return base_questions
