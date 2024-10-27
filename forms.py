from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo

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
