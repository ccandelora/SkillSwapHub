from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import join_room, leave_room, emit
from app import app, db, socketio
from models import (User, Skill, UserSkill, Message, TimeTransaction, VideoSession,
                   GroupClass, GroupClassParticipant, Challenge, ChallengeParticipant,
                   ChallengeUpdate)
from forms import (RegistrationForm, LoginForm, SkillForm, MessageForm,
                  GroupClassForm, ChallengeForm, ChallengeUpdateForm)
from utils.gemini_matcher import analyze_skill_compatibility, get_skill_recommendations
import json
import uuid
from datetime import datetime, timedelta

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            flash('Email already registered!')
            return redirect(url_for('register'))
        
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data)
        )
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please login.')
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
            return redirect(next_page if next_page else url_for('index'))
        flash('Invalid email or password')
        return redirect(url_for('login'))
    
    return render_template('login.html', form=form)

@app.route('/matches')
@login_required
def matches():
    user_skills = current_user.skills_teaching + current_user.skills_learning
    other_users = User.query.filter(User.id != current_user.id).all()
    
    matches = []
    for user in other_users:
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
    
    matches.sort(key=lambda x: x['score'], reverse=True)
    return render_template('matches.html', matches=matches)

@app.route('/video_sessions')
@login_required
def video_sessions():
    active_sessions = VideoSession.query.filter(
        ((VideoSession.teacher_id == current_user.id) | 
         (VideoSession.learner_id == current_user.id)) &
        (VideoSession.status.in_(['pending', 'active']))
    ).all()
    
    completed_sessions = VideoSession.query.filter(
        ((VideoSession.teacher_id == current_user.id) | 
         (VideoSession.learner_id == current_user.id)) &
        (VideoSession.status == 'completed')
    ).order_by(VideoSession.end_time.desc()).limit(10).all()
    
    return render_template('video_sessions.html',
                         active_sessions=active_sessions,
                         completed_sessions=completed_sessions)

@app.route('/search')
def search():
    try:
        query = request.args.get('q', '')
        skills = []
        if query:
            skills = Skill.query.filter(
                Skill.name.ilike(f'%{query}%')
            ).all()
        return render_template('search.html', skills=skills, query=query)
    except Exception as e:
        app.logger.error(f"Error in search: {str(e)}")
        flash('An error occurred while searching. Please try again.')
        return render_template('search.html', skills=[], query=query)

# Group Classes routes
@app.route('/classes')
@login_required
def classes():
    upcoming_classes = GroupClass.query.filter(
        GroupClass.start_time > datetime.utcnow(),
        GroupClass.status == 'scheduled'
    ).order_by(GroupClass.start_time).all()
    
    my_classes = GroupClass.query.filter(
        (GroupClass.creator_id == current_user.id) |
        GroupClass.participants.any(GroupClassParticipant.user_id == current_user.id)
    ).order_by(GroupClass.start_time.desc()).all()
    
    return render_template('classes.html',
                         upcoming_classes=upcoming_classes,
                         my_classes=my_classes)

@app.route('/join-class/<int:class_id>')
@login_required
def join_class(class_id):
    group_class = GroupClass.query.get_or_404(class_id)
    
    if len(group_class.participants) >= group_class.max_participants:
        flash('This class is full!')
        return redirect(url_for('classes'))
    
    existing = GroupClassParticipant.query.filter_by(
        class_id=class_id,
        user_id=current_user.id
    ).first()
    
    if existing:
        flash('You are already registered for this class!')
    else:
        participant = GroupClassParticipant()
        participant.class_id = class_id
        participant.user_id = current_user.id
        participant.attendance_status = 'registered'
        db.session.add(participant)
        db.session.commit()
        flash('Successfully joined the class!')
    
    return redirect(url_for('class_detail', class_id=class_id))

@app.route('/class/<int:class_id>')
@login_required
def class_detail(class_id):
    group_class = GroupClass.query.get_or_404(class_id)
    is_participant = GroupClassParticipant.query.filter_by(
        class_id=class_id,
        user_id=current_user.id
    ).first() is not None
    
    return render_template('class_detail.html',
                         group_class=group_class,
                         is_participant=is_participant,
                         now=datetime.utcnow())

@app.route('/create-class', methods=['GET', 'POST'])
@login_required
def create_class():
    form = GroupClassForm()
    form.skill_id.choices = [(s.id, s.name) for s in 
                            Skill.query.join(UserSkill)
                            .filter(UserSkill.teacher_id == current_user.id).all()]
    
    if form.validate_on_submit():
        group_class = GroupClass()
        group_class.title = form.title.data
        group_class.description = form.description.data
        group_class.skill_id = form.skill_id.data
        group_class.creator_id = current_user.id
        group_class.max_participants = form.max_participants.data
        group_class.start_time = form.start_time.data
        group_class.duration_minutes = form.duration_minutes.data
        group_class.room_id = str(uuid.uuid4())
        db.session.add(group_class)
        db.session.commit()
        flash('Class created successfully!')
        return redirect(url_for('classes'))
    
    return render_template('create_class.html', form=form)

# Challenges routes
@app.route('/challenges')
@login_required
def challenges():
    active_challenges = Challenge.query.filter_by(status='active').all()
    my_challenges = Challenge.query.filter(
        (Challenge.creator_id == current_user.id) |
        Challenge.participants.any(ChallengeParticipant.user_id == current_user.id)
    ).order_by(Challenge.end_date.desc()).all()
    
    return render_template('challenges.html',
                         active_challenges=active_challenges,
                         my_challenges=my_challenges)

@app.route('/create-challenge', methods=['GET', 'POST'])
@login_required
def create_challenge():
    form = ChallengeForm()
    form.skill_id.choices = [(s.id, s.name) for s in 
                            Skill.query.join(UserSkill)
                            .filter(UserSkill.teacher_id == current_user.id).all()]
    
    if form.validate_on_submit():
        challenge = Challenge()
        challenge.title = form.title.data
        challenge.description = form.description.data
        challenge.skill_id = form.skill_id.data
        challenge.creator_id = current_user.id
        challenge.start_date = form.start_date.data
        challenge.end_date = form.end_date.data
        challenge.goal_type = form.goal_type.data
        challenge.goal_value = form.goal_value.data
        challenge.status = 'upcoming' if form.start_date.data > datetime.now().date() else 'active'
        db.session.add(challenge)
        db.session.commit()
        flash('Challenge created successfully!')
        return redirect(url_for('challenges'))
    
    return render_template('create_challenge.html', form=form)

@app.route('/join-challenge/<int:challenge_id>')
@login_required
def join_challenge(challenge_id):
    challenge = Challenge.query.get_or_404(challenge_id)
    
    if challenge.end_date < datetime.now().date():
        flash('This challenge has ended!')
        return redirect(url_for('challenges'))
    
    existing = ChallengeParticipant.query.filter_by(
        challenge_id=challenge_id,
        user_id=current_user.id
    ).first()
    
    if existing:
        flash('You are already participating in this challenge!')
    else:
        participant = ChallengeParticipant()
        participant.challenge_id = challenge_id
        participant.user_id = current_user.id
        participant.current_progress = 0
        participant.completed = False
        db.session.add(participant)
        db.session.commit()
        flash('Successfully joined the challenge!')
    
    return redirect(url_for('challenge_detail', challenge_id=challenge_id))

@app.route('/challenge/<int:challenge_id>', methods=['GET', 'POST'])
@login_required
def challenge_detail(challenge_id):
    challenge = Challenge.query.get_or_404(challenge_id)
    participant = ChallengeParticipant.query.filter_by(
        challenge_id=challenge_id,
        user_id=current_user.id
    ).first()
    
    form = ChallengeUpdateForm() if participant and challenge.status == 'active' else None
    
    if form and form.validate_on_submit():
        update = ChallengeUpdate()
        update.participant_id = participant.id
        update.content = form.content.data
        update.progress_amount = form.progress_amount.data
        
        participant.current_progress += form.progress_amount.data
        if participant.current_progress >= challenge.goal_value:
            participant.completed = True
        
        db.session.add(update)
        db.session.commit()
        flash('Progress updated successfully!')
        return redirect(url_for('challenge_detail', challenge_id=challenge_id))
    
    updates = ChallengeUpdate.query.join(ChallengeParticipant).filter(
        ChallengeParticipant.challenge_id == challenge_id
    ).order_by(ChallengeUpdate.created_at.desc()).all()
    
    return render_template('challenge_detail.html',
                         challenge=challenge,
                         participant=participant,
                         form=form,
                         updates=updates)

@app.route('/profile/<username>')
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    recommendations = None
    if user == current_user:
        recommendations = json.loads(
            get_skill_recommendations(user.skills_teaching + user.skills_learning,
                                   Skill.query.all()) or '{}'
        )
    return render_template('profile.html', user=user, recommendations=recommendations)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/')
def index():
    featured_skills = Skill.query.limit(6).all()
    upcoming_classes = GroupClass.query.filter(
        GroupClass.start_time > datetime.utcnow(),
        GroupClass.status == 'scheduled'
    ).order_by(GroupClass.start_time).limit(3).all()
    
    active_challenges = Challenge.query.filter_by(
        status='active'
    ).order_by(Challenge.end_date).limit(3).all()
    
    return render_template('index.html',
                         featured_skills=featured_skills,
                         upcoming_classes=upcoming_classes,
                         active_challenges=active_challenges)

@app.context_processor
def utility_processor():
    def active_sessions_count():
        if current_user.is_authenticated:
            return VideoSession.query.filter(
                ((VideoSession.teacher_id == current_user.id) |
                 (VideoSession.learner_id == current_user.id)) &
                (VideoSession.status.in_(['pending', 'active']))
            ).count()
        return 0
    return dict(active_sessions_count=active_sessions_count())
