import markdown
from .gemini import generate_gemini_response

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
