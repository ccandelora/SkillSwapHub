import os
import google.generativeai as genai

# Configure Gemini
genai.configure(api_key=os.getenv('GOOGLE_GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-pro')

def analyze_skill_compatibility(teaching_skills, learning_skills):
    """
    Analyze the compatibility between teaching and learning skills using Gemini AI
    """
    prompt = f"""
    Analyze the compatibility between a potential teacher and learner based on their skills.
    
    Teaching Skills: {[skill.skill.name for skill in teaching_skills]}
    Learning Skills: {[skill.skill.name for skill in learning_skills]}
    
    Consider:
    1. Skill relevance and complementarity
    2. Skill level progression
    3. Natural skill groupings
    
    Return a JSON with:
    1. compatibility_score (0-100)
    2. reasoning (brief explanation)
    3. suggested_matches (list of specific skill pairs)
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error in Gemini API call: {e}")
        return None

def get_skill_recommendations(user_skills, available_skills):
    """
    Get personalized skill recommendations based on user's current skills
    """
    current_skills = [skill.skill.name for skill in user_skills]
    available_skill_names = [skill.name for skill in available_skills]
    
    prompt = f"""
    Based on a user's current skills, recommend complementary skills to learn.
    
    Current Skills: {current_skills}
    Available Skills: {available_skill_names}
    
    Consider:
    1. Natural skill progression paths
    2. Complementary skill combinations
    3. Industry-relevant skill groupings
    
    Return a JSON with:
    1. recommended_skills (list of top 5 skills)
    2. reasoning (brief explanation for each recommendation)
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error in Gemini API call: {e}")
        return None
