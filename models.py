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
    location = db.Column(db.String(128))  # Added for meetup functionality
    skills_teaching = db.relationship('UserSkill', backref='teacher',
                                    foreign_keys='UserSkill.teacher_id')
    skills_learning = db.relationship('UserSkill', backref='learner',
                                    foreign_keys='UserSkill.learner_id')
    achievements = db.relationship('UserAchievement', backref='user')
    created_classes = db.relationship('GroupClass', backref='creator',
                                    foreign_keys='GroupClass.creator_id')
    created_challenges = db.relationship('Challenge', backref='creator',
                                       foreign_keys='Challenge.creator_id')
    created_meetups = db.relationship('Meetup', backref='creator',
                                    foreign_keys='Meetup.creator_id')

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
    total_hours = db.Column(db.Float, default=0.0)
    last_session = db.Column(db.DateTime)
    sessions_completed = db.Column(db.Integer, default=0)

class Achievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.Text)
    badge_icon = db.Column(db.String(64))
    requirement_type = db.Column(db.String(32))
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
    status = db.Column(db.String(20), default='pending')
    duration_minutes = db.Column(db.Integer, nullable=True)

class TimeTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    learner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skill.id'), nullable=False)
    hours = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class GroupClass(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    skill_id = db.Column(db.Integer, db.ForeignKey('skill.id'), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    max_participants = db.Column(db.Integer, default=10)
    start_time = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, default=60)
    status = db.Column(db.String(20), default='scheduled')
    room_id = db.Column(db.String(64), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    skill = db.relationship('Skill')
    participants = db.relationship('GroupClassParticipant', backref='group_class')

class GroupClassParticipant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('group_class.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    attendance_status = db.Column(db.String(20), default='registered')
    
    user = db.relationship('User')

class Challenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    skill_id = db.Column(db.Integer, db.ForeignKey('skill.id'), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    goal_type = db.Column(db.String(20), nullable=False)
    goal_value = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='upcoming')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    skill = db.relationship('Skill')
    participants = db.relationship('ChallengeParticipant', backref='challenge')

class ChallengeParticipant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    current_progress = db.Column(db.Float, default=0)
    completed = db.Column(db.Boolean, default=False)
    
    user = db.relationship('User')

class ChallengeUpdate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(db.Integer, db.ForeignKey('challenge_participant.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    progress_amount = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    participant = db.relationship('ChallengeParticipant')

# New models for local meetups
class Meetup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    skill_id = db.Column(db.Integer, db.ForeignKey('skill.id'), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    location = db.Column(db.String(256), nullable=False)
    venue_details = db.Column(db.Text)
    max_participants = db.Column(db.Integer, default=10)
    date_time = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, default=120)
    status = db.Column(db.String(20), default='upcoming')  # upcoming, ongoing, completed, cancelled
    skill_level = db.Column(db.String(20), default='all')  # beginner, intermediate, advanced, all
    is_recurring = db.Column(db.Boolean, default=False)
    recurrence_pattern = db.Column(db.String(64))  # weekly, biweekly, monthly
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    skill = db.relationship('Skill')
    participants = db.relationship('MeetupParticipant', backref='meetup')

class MeetupParticipant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meetup_id = db.Column(db.Integer, db.ForeignKey('meetup.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role = db.Column(db.String(20), default='attendee')  # attendee, co-host
    rsvp_status = db.Column(db.String(20), default='going')  # going, maybe, not_going
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    attended = db.Column(db.Boolean, default=False)
    
    user = db.relationship('User')
