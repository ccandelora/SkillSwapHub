from datetime import datetime
from app import db
from models import Achievement, UserAchievement, UserSkill

# Define initial achievements
ACHIEVEMENTS = [
    {
        'name': 'First Steps',
        'description': 'Complete your first teaching session',
        'badge_icon': 'bi-stars',
        'requirement_type': 'teaching_sessions',
        'requirement_value': 1
    },
    {
        'name': 'Dedicated Teacher',
        'description': 'Reach 10 hours of teaching',
        'badge_icon': 'bi-award',
        'requirement_type': 'teaching_hours',
        'requirement_value': 10
    },
    {
        'name': 'Skill Collector',
        'description': 'Add 5 different skills to your profile',
        'badge_icon': 'bi-collection',
        'requirement_type': 'skills_count',
        'requirement_value': 5
    },
    {
        'name': 'Community Pillar',
        'description': 'Complete sessions with 10 different learners',
        'badge_icon': 'bi-people',
        'requirement_type': 'unique_learners',
        'requirement_value': 10
    },
    {
        'name': 'Expert Status',
        'description': 'Reach 50 hours of teaching a single skill',
        'badge_icon': 'bi-trophy',
        'requirement_type': 'single_skill_hours',
        'requirement_value': 50
    }
]

def initialize_achievements():
    """Initialize achievement records in the database"""
    for achievement_data in ACHIEVEMENTS:
        existing = Achievement.query.filter_by(name=achievement_data['name']).first()
        if not existing:
            achievement = Achievement(**achievement_data)
            db.session.add(achievement)
    db.session.commit()

def check_user_achievements(user_id):
    """Check and award any newly earned achievements for a user"""
    from models import User, VideoSession
    
    user = User.query.get(user_id)
    if not user:
        return []
    
    new_achievements = []
    
    # Get all achievements
    achievements = Achievement.query.all()
    
    for achievement in achievements:
        # Skip if already earned
        if UserAchievement.query.filter_by(
            user_id=user_id, 
            achievement_id=achievement.id
        ).first():
            continue
            
        earned = False
        
        if achievement.requirement_type == 'teaching_sessions':
            completed_sessions = VideoSession.query.filter_by(
                teacher_id=user_id,
                status='completed'
            ).count()
            earned = completed_sessions >= achievement.requirement_value
            
        elif achievement.requirement_type == 'teaching_hours':
            total_hours = sum(skill.total_hours for skill in user.skills_teaching)
            earned = total_hours >= achievement.requirement_value
            
        elif achievement.requirement_type == 'skills_count':
            skills_count = UserSkill.query.filter_by(teacher_id=user_id).count()
            earned = skills_count >= achievement.requirement_value
            
        elif achievement.requirement_type == 'unique_learners':
            unique_learners = db.session.query(VideoSession.learner_id).filter_by(
                teacher_id=user_id,
                status='completed'
            ).distinct().count()
            earned = unique_learners >= achievement.requirement_value
            
        elif achievement.requirement_type == 'single_skill_hours':
            max_hours = db.session.query(db.func.max(UserSkill.total_hours)).filter_by(
                teacher_id=user_id
            ).scalar() or 0
            earned = max_hours >= achievement.requirement_value
            
        if earned:
            user_achievement = UserAchievement(
                user_id=user_id,
                achievement_id=achievement.id,
                earned_at=datetime.utcnow()
            )
            db.session.add(user_achievement)
            new_achievements.append(achievement)
            
    if new_achievements:
        db.session.commit()
        
    return new_achievements

def update_skill_progress(session):
    """Update skill progress after a completed video session"""
    if session.status != 'completed' or not session.duration_minutes:
        return
        
    # Update teacher's progress
    teacher_skill = UserSkill.query.filter_by(
        teacher_id=session.teacher_id,
        skill_id=session.skill_id
    ).first()
    
    if teacher_skill:
        teacher_skill.total_hours += session.duration_minutes / 60
        teacher_skill.sessions_completed += 1
        teacher_skill.last_session = session.end_time
        
    # Update learner's progress
    learner_skill = UserSkill.query.filter_by(
        learner_id=session.learner_id,
        skill_id=session.skill_id
    ).first()
    
    if learner_skill:
        learner_skill.total_hours += session.duration_minutes / 60
        learner_skill.sessions_completed += 1
        learner_skill.last_session = session.end_time
        
    db.session.commit()
    
    # Check for new achievements
    check_user_achievements(session.teacher_id)
    check_user_achievements(session.learner_id)
