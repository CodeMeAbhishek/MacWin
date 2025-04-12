import google.generativeai as genai
import os

# Set your Gemini API key here or through env variable
genai.configure(api_key="AIzaSyBkw13CxnE61t7odM2umxLYm162Ywsf7XE")

model = genai.GenerativeModel("gemini-2.0-flash")

def get_career_advice(name, skills, experience):
    prompt = f"""
    User Profile:
    Name: {name}
    Skills: {skills}
    Experience: {experience} years

    Based on the above profile:
    1. Suggest 2–3 ideal tech career paths and explain why they're a good fit.
    2. Recommend 1 skill the user should learn next and why.
    Be concise and professional.
    """
    response = model.generate_content(prompt)
    return response.text

def generate_gemini_response(prompt):
    response = model.generate_content(prompt)
    return response.text

def generate_quiz_question(name, skills, experience, previous_qas, role_context="", age_context=""):
    prompt = f"""
    You are generating a career-related dynamic quiz. 
    The user is: {name}, with skills: {skills}, and {experience} years of experience.
    
    {role_context}
    {age_context}
    
    Here are previous questions and answers:
    {previous_qas}
    
    Now ask the next question to better understand their background, goals, or preferences.
    The question should be relevant to their role and age group.
    Return only the question text.
    """
    response = model.generate_content(prompt)
    return response.text

def get_ai_dashboard_insights(user, quiz_answers):
    prompt = f"""
    User Profile:
    Name: {user.name}
    Role: {user.role if hasattr(user, 'role') else 'Not specified'}
    Age: {user.age if hasattr(user, 'age') else 'Not specified'}
    Experience: {user.years_of_experience} years
    Skills: {user.skills}

    Quiz Responses:
    {'; '.join(quiz_answers)}

    Based on this information, generate a comprehensive career development plan including:

    1. Career Path Analysis:
       - Top 3 recommended career paths based on skills and experience
       - Detailed explanation of why each path is suitable
       - Required skills and qualifications for each path

    2. Skill Development:
       - Current skill strengths and gaps
       - Specific skills to develop next
       - Recommended learning resources (free and paid)
       - Timeline for skill development

    3. Professional Growth:
       - Industry trends to watch
       - Networking opportunities
       - Relevant communities and events
       - GitHub projects to contribute to

    4. Action Plan:
       - Immediate next steps (next 30 days)
       - Medium-term goals (3-6 months)
       - Long-term career trajectory
       - Key milestones to track

    Format the response in a clear, structured way with sections and bullet points.
    Be specific and practical in your recommendations.
    Focus on actionable insights that the user can implement immediately.
    """
    response = model.generate_content(prompt)
    return response.text

def generate_dynamic_quiz(user):
    # Get role-specific context
    role_contexts = {
        'Student': "Focus on academic path, internships, and early career preparation",
        'Teacher': "Focus on educational technology, teaching methods, and career advancement in education",
        'Job-seeker': "Focus on job market trends, skill requirements, and career transitions",
        'Individual': "Focus on general career growth and skill development"
    }

    # Get age-specific context
    def get_age_context(age):
        if age < 20:
            return "early career planning and education choices"
        elif age < 25:
            return "entry-level positions and skill development"
        elif age < 35:
            return "career growth and specialization"
        else:
            return "career advancement and leadership opportunities"

    role_context = role_contexts.get(user.role, role_contexts['Individual'])
    age_context = get_age_context(user.age) if user.age else "career development"

    prompt = f"""
    Generate exactly 3 personalized career-related questions for the following user profile:

    Name: {user.name}
    Role: {user.role if user.role else 'Not specified'}
    Age: {user.age if user.age else 'Not specified'}
    Experience: {user.years_of_experience} years
    Skills: {user.skills}

    Context:
    - Role Focus: {role_context}
    - Age Focus: {age_context}

    The questions should:
    1. Be highly relevant to their specific role ({user.role}) and age group
    2. Help understand their career goals and preferences
    3. Be specific to their current skill set and experience level
    4. Consider their life stage and career phase
    5. Be open-ended to encourage detailed responses
    6. Help gather information for personalized career advice

    Format your response EXACTLY like this:
    1. [First question here]
    2. [Second question here]
    3. [Third question here]

    Make each question detailed and specific to their role and age group.
    Do not include any other text in your response.
    """
    response = model.generate_content(prompt)
    questions = [q.strip() for q in response.text.strip().split('\n') if q.strip()]
    
    # Ensure we have exactly 3 questions
    if len(questions) < 3:
        # Generate additional questions if needed
        additional_prompt = f"Generate {3 - len(questions)} more questions following the same criteria."
        additional_response = model.generate_content(additional_prompt)
        additional_questions = [q.strip() for q in additional_response.text.strip().split('\n') if q.strip()]
        questions.extend(additional_questions[:3 - len(questions)])
    
    # Format questions properly
    formatted_questions = []
    for i, q in enumerate(questions[:3], 1):
        # Remove any leading numbers or dots
        q = q.lstrip('0123456789. ')
        formatted_questions.append(f"{i}. {q}")
    
    return formatted_questions