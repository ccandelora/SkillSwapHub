from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, db
from models import User, Skill, UserSkill, Message, TimeTransaction
from forms import RegistrationForm, LoginForm, SkillForm, MessageForm

@app.route('/')
def index():
    featured_skills = Skill.query.limit(6).all()
    return render_template('index.html', featured_skills=featured_skills)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data,
                   email=form.email.data,
                   password_hash=generate_password_hash(form.password.data))
        db.session.add(user)
        db.session.commit()
        flash('Registration successful!')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

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

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/profile/<username>')
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('profile.html', user=user)

@app.route('/search')
def search():
    query = request.args.get('q', '')
    skills = Skill.query.filter(Skill.name.ilike(f'%{query}%')).all()
    return render_template('search.html', skills=skills, query=query)

@app.route('/matches')
@login_required
def matches():
    user_teaching_skills = UserSkill.query.filter_by(
        teacher_id=current_user.id).all()
    user_learning_skills = UserSkill.query.filter_by(
        learner_id=current_user.id).all()
    matches = []
    for teaching in user_teaching_skills:
        potential_learners = UserSkill.query.filter_by(
            skill_id=teaching.skill_id,
            is_teaching=False).all()
        matches.extend(potential_learners)
    return render_template('matches.html', matches=matches)

@app.route('/chat/<int:user_id>', methods=['GET', 'POST'])
@login_required
def chat(user_id):
    other_user = User.query.get_or_404(user_id)
    form = MessageForm()
    if form.validate_on_submit():
        message = Message(sender_id=current_user.id,
                        recipient_id=user_id,
                        content=form.content.data)
        db.session.add(message)
        db.session.commit()
        return redirect(url_for('chat', user_id=user_id))
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & 
         (Message.recipient_id == user_id)) |
        ((Message.sender_id == user_id) & 
         (Message.recipient_id == current_user.id))
    ).order_by(Message.timestamp.asc()).all()
    return render_template('chat.html', 
                         other_user=other_user,
                         messages=messages,
                         form=form)
