import markdown
from .gemini import generate_gemini_response
import re

def clean_markdown(text):
    # Remove excessive asterisks and other markdown artifacts
    text = re.sub(r'\*\*Note:\*\*', 'Note:', text)
    text = re.sub(r'\*\*Path \d+:', 'Path:', text)
    text = re.sub(r'\*\*Required Skills', 'Required Skills', text)
    text = re.sub(r'\*\*Suitability:\*\*', 'Suitability:', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\#{2,}', '', text)  # Remove multiple hashtags
    text = re.sub(r'\*\s+', '• ', text)  # Convert asterisk lists to bullet points
    return text

def get_resume_feedback(resume_text):
    prompt = f"""
Analyze the following resume and provide:

1. Five specific improvement suggestions
2. Three interview tips tailored to this resume

Format your response with clear sections and bullet points.
Avoid using markdown symbols - use plain text with simple formatting.

Resume:
\"\"\"
{resume_text}
\"\"\"
"""
    raw_response = generate_gemini_response(prompt)
    cleaned_response = clean_markdown(raw_response)
    html_response = markdown.markdown(cleaned_response)
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
