from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db, socketio
from models import User, Skill, UserSkill, Message, VideoSession
from utils.gemini_matcher import analyze_skill_compatibility, get_skill_recommendations
import json

@app.route('/matches')
@login_required
def matches():
    try:
        user_skills = current_user.skills_teaching + current_user.skills_learning
        other_users = User.query.filter(User.id != current_user.id).all()
        
        matches = []
        for user in other_users:
            try:
                other_skills = user.skills_teaching + user.skills_learning
                compatibility = {
                    'as_teacher': json.loads(analyze_skill_compatibility(current_user.skills_teaching, user.skills_learning) or '{}'),
                    'as_learner': json.loads(analyze_skill_compatibility(user.skills_teaching, current_user.skills_learning) or '{}')
                }
                
                score = (compatibility['as_teacher'].get('compatibility_score', 0) + 
                        compatibility['as_learner'].get('compatibility_score', 0)) / 2
                        
                if score > 0:
                    matches.append({
                        'user': user,
                        'compatibility': compatibility,
                        'score': score
                    })
            except Exception as e:
                app.logger.error(f"Error processing match for user {user.id}: {str(e)}")
                continue
        
        matches.sort(key=lambda x: x['score'], reverse=True)
        return render_template('matches.html', matches=matches)
        
    except Exception as e:
        app.logger.error(f"Error in matches route: {str(e)}")
        flash("An error occurred while finding matches. Please try again later.", "error")
        return redirect(url_for('index'))
