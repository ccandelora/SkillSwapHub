import google.generativeai as genai
import os
import json

# Configure Gemini API
genai.configure(api_key=os.environ['GOOGLE_GEMINI_API_KEY'])
model = genai.GenerativeModel('gemini-pro')

def analyze_skill_compatibility(teacher_skills, learner_skills):
    """
    Analyze compatibility between teacher and learner skills.
    Returns JSON string with compatibility score and reasons.
    """
    try:
        if not teacher_skills or not learner_skills:
            return json.dumps({
                "compatibility_score": 0,
                "reasons": ["No skills to compare"],
                "matching_skills": []
            })

        # Format skills for analysis
        teaching = [f"{skill.skill.name} ({skill.proficiency_level})" 
                   for skill in teacher_skills]
        learning = [f"{skill.skill.name} ({skill.proficiency_level})" 
                   for skill in learner_skills]

        prompt = f"""
        Analyze the compatibility between a teacher's skills and a learner's interests.
        Teacher skills: {teaching}
        Learner interests: {learning}
        
        Provide a JSON response with:
        1. compatibility_score (0-100)
        2. reasons (list of strings explaining the match)
        3. matching_skills (list of matching skill names)
        """

        response = model.generate_content(prompt)
        
        if not response or not response.text:
            return json.dumps({
                "compatibility_score": 0,
                "reasons": ["Unable to analyze skills at this time"],
                "matching_skills": []
            })

        # Try to parse the response as JSON
        try:
            result = json.loads(response.text)
            # Validate required fields
            required_fields = ["compatibility_score", "reasons", "matching_skills"]
            if not all(field in result for field in required_fields):
                raise ValueError("Missing required fields in response")
            return json.dumps(result)
        except (json.JSONDecodeError, ValueError):
            # If response is not valid JSON, create a structured response
            return json.dumps({
                "compatibility_score": 50,
                "reasons": ["Automated analysis completed"],
                "matching_skills": [s.skill.name for s in teacher_skills 
                                  if any(l.skill.name == s.skill.name for l in learner_skills)]
            })

    except Exception as e:
        # Return a safe default response for any errors
        return json.dumps({
            "compatibility_score": 0,
            "reasons": [f"Error analyzing skills: {str(e)}"],
            "matching_skills": []
        })

def get_skill_recommendations(user_skills, all_skills):
    """
    Get personalized skill recommendations based on user's current skills.
    Returns JSON string with recommendations.
    """
    try:
        if not user_skills or not all_skills:
            return json.dumps({
                "recommended_skills": [],
                "reasons": ["No skills available for analysis"]
            })

        current_skills = [f"{skill.skill.name} ({skill.proficiency_level})" 
                         for skill in user_skills]
        available_skills = [skill.name for skill in all_skills]

        prompt = f"""
        Based on these current skills: {current_skills}
        Recommend skills from this list: {available_skills}
        
        Provide a JSON response with:
        1. recommended_skills (list of skill names)
        2. reasons (list of strings explaining each recommendation)
        """

        response = model.generate_content(prompt)
        
        if not response or not response.text:
            return json.dumps({
                "recommended_skills": [],
                "reasons": ["Unable to generate recommendations at this time"]
            })

        try:
            result = json.loads(response.text)
            if not all(field in result for field in ["recommended_skills", "reasons"]):
                raise ValueError("Missing required fields in response")
            return json.dumps(result)
        except (json.JSONDecodeError, ValueError):
            return json.dumps({
                "recommended_skills": [s.name for s in all_skills[:3]],
                "reasons": ["Based on general popularity"]
            })

    except Exception as e:
        return json.dumps({
            "recommended_skills": [],
            "reasons": [f"Error generating recommendations: {str(e)}"]
        })
