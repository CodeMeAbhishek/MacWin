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

def generate_quiz_question(name, skills, experience, previous_qas):
    prompt = f"""
    You are generating a career-related dynamic quiz. 
    The user is: {name}, with skills: {skills}, and {experience} years of experience.
    
    Here are previous questions and answers:
    {previous_qas}
    
    Now ask the next question to better understand their background, goals, or preferences.
    Return only the question text.
    """
    response = model.generate_content(prompt)
    return response.text
