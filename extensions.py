# extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# We initialize them here cleanly, away from the app.py execution engine
db = SQLAlchemy()
login_manager = LoginManager()