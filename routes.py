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

# Existing routes...
# [Previous route definitions remain unchanged]

# New routes for group classes
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

@app.route('/create-class', methods=['GET', 'POST'])
@login_required
def create_class():
    form = GroupClassForm()
    form.skill_id.choices = [(s.id, s.name) for s in 
                            Skill.query.join(UserSkill)
                            .filter(UserSkill.teacher_id == current_user.id).all()]
    
    if form.validate_on_submit():
        group_class = GroupClass(
            title=form.title.data,
            description=form.description.data,
            skill_id=form.skill_id.data,
            creator_id=current_user.id,
            max_participants=form.max_participants.data,
            start_time=form.start_time.data,
            duration_minutes=form.duration_minutes.data,
            room_id=str(uuid.uuid4())
        )
        db.session.add(group_class)
        db.session.commit()
        flash('Class created successfully!')
        return redirect(url_for('classes'))
    
    return render_template('create_class.html', form=form)

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
        participant = GroupClassParticipant(
            class_id=class_id,
            user_id=current_user.id
        )
        db.session.add(participant)
        db.session.commit()
        flash('Successfully joined the class!')
    
    return redirect(url_for('classes'))

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
                         is_participant=is_participant)

# Routes for challenges
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
    form.skill_id.choices = [(s.id, s.name) for s in Skill.query.all()]
    
    if form.validate_on_submit():
        challenge = Challenge(
            title=form.title.data,
            description=form.description.data,
            skill_id=form.skill_id.data,
            creator_id=current_user.id,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            goal_type=form.goal_type.data,
            goal_value=form.goal_value.data,
            status='upcoming' if form.start_date.data > datetime.now().date() else 'active'
        )
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
        participant = ChallengeParticipant(
            challenge_id=challenge_id,
            user_id=current_user.id
        )
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
    
    form = ChallengeUpdateForm() if participant else None
    
    if form and form.validate_on_submit():
        update = ChallengeUpdate(
            participant_id=participant.id,
            content=form.content.data,
            progress_amount=form.progress_amount.data
        )
        
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

# Update the index route to include featured classes and challenges
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
