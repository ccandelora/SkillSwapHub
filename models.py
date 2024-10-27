from app import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    bio = db.Column(db.Text)
    time_credits = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    skills_teaching = db.relationship('UserSkill', backref='teacher',
                                    foreign_keys='UserSkill.teacher_id')
    skills_learning = db.relationship('UserSkill', backref='learner',
                                    foreign_keys='UserSkill.learner_id')
    achievements = db.relationship('UserAchievement', backref='user')

class Skill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    category = db.Column(db.String(64))
    description = db.Column(db.Text)

class UserSkill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    skill_id = db.Column(db.Integer, db.ForeignKey('skill.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    learner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    proficiency_level = db.Column(db.String(20))
    is_teaching = db.Column(db.Boolean, default=False)
    skill = db.relationship('Skill')
    # Add progression tracking fields
    total_hours = db.Column(db.Float, default=0.0)
    last_session = db.Column(db.DateTime)
    sessions_completed = db.Column(db.Integer, default=0)

class Achievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.Text)
    badge_icon = db.Column(db.String(64))  # Bootstrap icon class name
    requirement_type = db.Column(db.String(32))  # e.g., 'teaching_hours', 'sessions', 'skills'
    requirement_value = db.Column(db.Integer)

class UserAchievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievement.id'), nullable=False)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)
    achievement = db.relationship('Achievement')

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)
    is_video_call = db.Column(db.Boolean, default=False)
    video_room_id = db.Column(db.String(64), nullable=True)

class VideoSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.String(64), unique=True, nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    learner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skill.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, active, completed
    duration_minutes = db.Column(db.Integer, nullable=True)

class TimeTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    learner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skill.id'), nullable=False)
    hours = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
