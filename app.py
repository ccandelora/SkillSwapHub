from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(id):
    from models import User
    return User.query.get(int(id))

# Register blueprints
from routes.subscription import bp as subscription_bp
app.register_blueprint(subscription_bp, url_prefix='/subscription')

# Import routes after app initialization to avoid circular imports
from routes import *
