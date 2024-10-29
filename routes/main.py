from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import func
from app import db
from models import User, Skill, UserSkill
from forms import LoginForm, RegistrationForm, SkillForm
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from utils.gemini_matcher import get_skill_recommendations

routes_bp = Blueprint('main', __name__)

@routes_bp.route('/')
def index():
    """Landing page route"""
    try:
        # Get popular skills for showcase
        popular_skills = db.session.query(
            Skill,
            func.count(UserSkill.id).label('user_count')
        ).outerjoin(UserSkill).group_by(Skill.id).order_by(func.count(UserSkill.id).desc()).limit(6).all()

        # Format popular skills data
        popular_skills_data = []
        for skill, count in popular_skills:
            popular_skills_data.append({
                'name': skill.name,
                'user_count': count
            })

        context = {
            'popular_skills': popular_skills_data
        }

        # Add authenticated user specific data
        if current_user.is_authenticated:
            teaching_skills = UserSkill.query.filter_by(
                teacher_id=current_user.id
            ).all()
            
            learning_skills = UserSkill.query.filter_by(
                learner_id=current_user.id
            ).all()
            
            all_skills = Skill.query.all()
            recommendations = get_skill_recommendations(learning_skills, all_skills)
            
            context.update({
                'teaching_skills': teaching_skills,
                'learning_skills': learning_skills,
                'recommendations': recommendations
            })

        return render_template('index.html', **context)

    except Exception as e:
        current_app.logger.error(f"Error in index route: {str(e)}")
        return render_template('index.html', popular_skills=[])

@routes_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data or ''):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        flash('Invalid email or password')
    return render_template('login.html', form=form)

@routes_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered')
            return redirect(url_for('main.register'))
        
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already taken')
            return redirect(url_for('main.register'))
        
        user = User()
        user.username = form.username.data
        user.email = form.email.data
        user.password_hash = generate_password_hash(form.password.data or '')
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful')
        return redirect(url_for('main.login'))
    return render_template('register.html', form=form)

@routes_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@routes_bp.route('/add_skill', methods=['GET', 'POST'])
@login_required
def add_skill():
    form = SkillForm()
    if form.validate_on_submit():
        # Check if skill exists or create new one
        skill = Skill.query.filter_by(name=form.skill_name.data).first()
        if not skill:
            skill = Skill()
            skill.name = form.skill_name.data
            db.session.add(skill)
        
        # Create user skill relationship
        user_skill = UserSkill()
        user_skill.skill = skill
        user_skill.proficiency_level = form.proficiency_level.data
        user_skill.is_teaching = form.is_teaching.data
        
        if form.is_teaching.data:
            user_skill.teacher_id = current_user.id
        else:
            user_skill.learner_id = current_user.id
        
        db.session.add(user_skill)
        db.session.commit()
        
        flash('Skill added successfully')
        return redirect(url_for('main.index'))
    return render_template('add_skill.html', form=form)
