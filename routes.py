from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import join_room, leave_room, emit
from app import app, db, socketio
from models import User, Skill, UserSkill, Message, TimeTransaction, VideoSession
from forms import RegistrationForm, LoginForm, SkillForm, MessageForm
from utils.gemini_matcher import analyze_skill_compatibility, get_skill_recommendations
import json
import uuid

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

@app.route('/add_skill', methods=['GET', 'POST'])
@login_required
def add_skill():
    form = SkillForm()
    existing_skills = Skill.query.all()
    
    if form.validate_on_submit():
        skill = Skill.query.filter_by(name=form.skill_name.data).first()
        if not skill:
            skill = Skill(name=form.skill_name.data, description=form.description.data)
            db.session.add(skill)
            db.session.flush()
        
        existing_user_skill = UserSkill.query.filter_by(
            skill_id=skill.id,
            teacher_id=current_user.id if form.is_teaching.data else None,
            learner_id=current_user.id if not form.is_teaching.data else None
        ).first()
        
        if existing_user_skill:
            flash('You already have this skill listed!')
        else:
            user_skill = UserSkill(
                skill_id=skill.id,
                teacher_id=current_user.id if form.is_teaching.data else None,
                learner_id=current_user.id if not form.is_teaching.data else None,
                proficiency_level=form.proficiency_level.data,
                is_teaching=form.is_teaching.data
            )
            db.session.add(user_skill)
            
            try:
                db.session.commit()
                flash('Skill added successfully!')
                return redirect(url_for('profile', username=current_user.username))
            except Exception as e:
                db.session.rollback()
                flash('An error occurred while adding the skill.')
                print(f"Error: {e}")
                
    return render_template('add_skill.html', form=form, existing_skills=existing_skills)

@app.route('/profile/<username>')
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    if user == current_user:
        all_skills = Skill.query.all()
        recommendations = get_skill_recommendations(user.skills_learning, all_skills)
        try:
            recommendations = json.loads(recommendations) if recommendations else {}
        except:
            recommendations = {}
    else:
        recommendations = {}
    return render_template('profile.html', user=user, recommendations=recommendations)

@app.route('/search')
def search():
    query = request.args.get('q', '')
    skills = Skill.query.filter(Skill.name.ilike(f'%{query}%')).all()
    return render_template('search.html', skills=skills, query=query)

@app.route('/matches')
@login_required
def matches():
    user_teaching_skills = UserSkill.query.filter_by(teacher_id=current_user.id).all()
    user_learning_skills = UserSkill.query.filter_by(learner_id=current_user.id).all()
    
    matches = []
    potential_users = User.query.filter(User.id != current_user.id).all()
    
    for user in potential_users:
        their_teaching = UserSkill.query.filter_by(teacher_id=user.id).all()
        their_learning = UserSkill.query.filter_by(learner_id=user.id).all()
        
        compatibility_as_teacher = analyze_skill_compatibility(
            user_teaching_skills, their_learning
        )
        compatibility_as_learner = analyze_skill_compatibility(
            their_teaching, user_learning_skills
        )
        
        try:
            compatibility_as_teacher = json.loads(compatibility_as_teacher) if compatibility_as_teacher else {}
            compatibility_as_learner = json.loads(compatibility_as_learner) if compatibility_as_learner else {}
            
            overall_score = (
                int(compatibility_as_teacher.get('compatibility_score', 0)) +
                int(compatibility_as_learner.get('compatibility_score', 0))
            ) / 2
            
            if overall_score > 30:
                matches.append({
                    'user': user,
                    'score': overall_score,
                    'compatibility': {
                        'as_teacher': compatibility_as_teacher,
                        'as_learner': compatibility_as_learner
                    }
                })
        except:
            continue
    
    matches.sort(key=lambda x: x['score'], reverse=True)
    return render_template('matches.html', matches=matches)

@app.route('/video/<int:user_id>/<int:skill_id>')
@login_required
def video_chat(user_id, skill_id):
    other_user = User.query.get_or_404(user_id)
    skill = Skill.query.get_or_404(skill_id)
    
    session = VideoSession.query.filter_by(
        teacher_id=other_user.id,
        learner_id=current_user.id,
        skill_id=skill_id,
        status='pending'
    ).first()
    
    if not session:
        session = VideoSession(
            room_id=str(uuid.uuid4()),
            teacher_id=other_user.id,
            learner_id=current_user.id,
            skill_id=skill_id
        )
        db.session.add(session)
        db.session.commit()
    
    return render_template('video_chat.html', 
                         other_user=other_user,
                         skill=skill,
                         room_id=session.room_id)

@socketio.on('join')
def on_join(data):
    room = data['roomId']
    join_room(room)
    emit('user-connected', room=room)

@socketio.on('leave-room')
def on_leave(data):
    room = data['roomId']
    leave_room(room)
    emit('user-disconnected', room=room)

@socketio.on('offer')
def on_offer(data):
    emit('offer', data['offer'], room=data['roomId'])

@socketio.on('answer')
def on_answer(data):
    emit('answer', data['answer'], room=data['roomId'])

@socketio.on('ice-candidate')
def on_ice_candidate(data):
    emit('ice-candidate', data['candidate'], room=data['roomId'])

@app.route('/chat/<int:user_id>', methods=['GET', 'POST'])
@login_required
def chat(user_id):
    other_user = User.query.get_or_404(user_id)
    form = MessageForm()
    
    teachable_skills = UserSkill.query.filter_by(
        teacher_id=other_user.id,
        is_teaching=True
    ).all()
    
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
                         form=form,
                         teachable_skills=teachable_skills)