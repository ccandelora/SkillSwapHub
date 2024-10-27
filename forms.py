from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, BooleanField, IntegerField, DateTimeLocalField, DateField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange, ValidationError
from datetime import datetime

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', 
                                   validators=[DataRequired(), EqualTo('password')])

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')

class SkillForm(FlaskForm):
    skill_name = StringField('Skill Name', validators=[DataRequired()])
    proficiency_level = SelectField('Proficiency Level',
                                  choices=[('beginner', 'Beginner'),
                                         ('intermediate', 'Intermediate'),
                                         ('advanced', 'Advanced')])
    is_teaching = BooleanField('I can teach this')
    description = TextAreaField('Description')

class MessageForm(FlaskForm):
    content = TextAreaField('Message', validators=[DataRequired()])

# New forms for group classes and challenges
class GroupClassForm(FlaskForm):
    title = StringField('Class Title', validators=[DataRequired(), Length(max=128)])
    description = TextAreaField('Description', validators=[DataRequired()])
    skill_id = SelectField('Skill', coerce=int, validators=[DataRequired()])
    max_participants = IntegerField('Maximum Participants', 
                                  validators=[DataRequired(), NumberRange(min=2, max=50)],
                                  default=10)
    start_time = DateTimeLocalField('Start Time', 
                                  format='%Y-%m-%dT%H:%M',
                                  validators=[DataRequired()])
    duration_minutes = IntegerField('Duration (minutes)', 
                                  validators=[DataRequired(), NumberRange(min=30, max=180)],
                                  default=60)

    def validate_start_time(self, field):
        if field.data < datetime.now():
            raise ValidationError('Start time must be in the future')

class ChallengeForm(FlaskForm):
    title = StringField('Challenge Title', validators=[DataRequired(), Length(max=128)])
    description = TextAreaField('Description', validators=[DataRequired()])
    skill_id = SelectField('Skill', coerce=int, validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    goal_type = SelectField('Goal Type',
                          choices=[('hours', 'Hours of Practice'),
                                 ('sessions', 'Number of Sessions'),
                                 ('tasks', 'Completed Tasks')],
                          validators=[DataRequired()])
    goal_value = IntegerField('Goal Value', 
                            validators=[DataRequired(), NumberRange(min=1)])

    def validate_end_date(self, field):
        if self.start_date.data and field.data < self.start_date.data:
            raise ValidationError('End date must be after start date')
        if self.start_date.data and self.start_date.data < datetime.now().date():
            raise ValidationError('Start date must be in the future')

class ChallengeUpdateForm(FlaskForm):
    content = TextAreaField('Update Description', validators=[DataRequired()])
    progress_amount = IntegerField('Progress Amount', validators=[NumberRange(min=0)])
