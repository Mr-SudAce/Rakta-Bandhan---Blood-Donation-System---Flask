from flask import Flask
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from models import db, User
import os


HARDCODED_USER = "Crusher"
HARDCODED_PASS = "Raw@123"
HARDCODED_EMAIL = "raw@example.com"
HARDCODED_PHONE = "0000000000"
HARDCODED_BLOOD_GRP = "A+"
HARDCODED_ADDRESS = "Admin Address"
HARDCODED_PROFILE_PIC = "{{ url_for('static', filename='profile_pics/admin_dflt.jpg') }}"
HARDCODED_ROLE = "superadmin"

# Mapping flash categories to Bootstrap alert classes
flash_categories = {
    "error": "danger",
    "info": "info",
    "warning": "warning",
    "success": "success",
    "primary": "primary",
    "secondary": "secondary",
}

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.abspath(os.path.dirname(__file__)), 'rakta_bandhan.db')}"
db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    if not user_id or user_id == "None":
        return None
    return User.query.get(int(user_id))

@app.context_processor
def inject_name():
    if current_user.is_authenticated:
        role = current_user.role.capitalize()
        return dict(name=f"{current_user.username} ({role})")
    return dict(name="")

@app.context_processor
def utility_processor():
    return dict(flash_categories=flash_categories)


from routes import *


if __name__ == '__main__':
    app.run(debug=True)