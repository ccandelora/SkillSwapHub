from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import func, or_, and_
from app import app, db
from models import User, Skill, UserSkill, Message, VideoSession, Achievement
from forms import LoginForm, RegistrationForm, SkillForm
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

@app.route('/')
def index():
    """Landing page route"""
    return render_template('index.html')

@app.route('/search')
@login_required
def search():
    """Search for skills and users"""
    # Get search parameters
    skill_query = request.args.get('skill', '').strip()
    proficiency = request.args.get('proficiency', '').strip()
    teaching = request.args.get('teaching', 'teachers').strip()
    
    # Base query
    query = UserSkill.query.join(Skill).join(User)
    
    # Apply filters
    if skill_query:
        query = query.filter(Skill.name.ilike(f'%{skill_query}%'))
    if proficiency:
        query = query.filter(UserSkill.proficiency_level == proficiency)
    
    # Filter by teaching/learning status
    query = query.filter(UserSkill.is_teaching == (teaching == 'teachers'))
    
    # Get results
    skills = query.order_by(UserSkill.total_hours.desc()).limit(20).all()
    
    # Get popular skills
    popular_skills = db.session.query(
        Skill,
        func.count(UserSkill.id).filter(UserSkill.is_teaching == True).label('teacher_count'),
        func.count(UserSkill.id).filter(UserSkill.is_teaching == False).label('learner_count')
    ).join(UserSkill).group_by(Skill.id).order_by(func.count(UserSkill.id).desc()).limit(8).all()
    
    return render_template('search.html', 
                         skills=skills,
                         popular_skills=[{
                             'name': skill.name,
                             'teacher_count': teacher_count,
                             'learner_count': learner_count
                         } for skill, teacher_count, learner_count in popular_skills])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        flash('Invalid email or password')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already taken')
            return redirect(url_for('register'))
        
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data)
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/add_skill', methods=['GET', 'POST'])
@login_required
def add_skill():
    form = SkillForm()
    if form.validate_on_submit():
        # Check if skill exists or create new one
        skill = Skill.query.filter_by(name=form.skill_name.data).first()
        if not skill:
            skill = Skill(name=form.skill_name.data)
            db.session.add(skill)
        
        # Create user skill relationship
        user_skill = UserSkill(
            skill=skill,
            proficiency_level=form.proficiency_level.data,
            is_teaching=form.is_teaching.data,
            teacher=current_user if form.is_teaching.data else None,
            learner=current_user if not form.is_teaching.data else None
        )
        db.session.add(user_skill)
        db.session.commit()
        
        flash('Skill added successfully')
        return redirect(url_for('index'))
    return render_template('add_skill.html', form=form)
