# ------------------- IMPORTS & CONSTANTS -------------------
from flask import Flask
from flask_login import current_user
import os
from extensions import db, migrate, login_manager
from main_app.models import User
from werkzeug.security import generate_password_hash

# ------------------- HARD-CODED SUPERADMIN -------------------
HARDCODED_USER = "Crusher"
HARDCODED_PASS = "Raw@123"
HARDCODED_EMAIL = "raw@example.com"
HARDCODED_PHONE = "0000000000"
HARDCODED_BLOOD_GRP = "--"
HARDCODED_DOB = "2000-01-01"
HARDCODED_GENDER = "None"
HARDCODED_ADDRESS = "Admin Address"
HARDCODED_PROFILE_PIC = "profile_pics/static_images/admin_dflt.jpg"
HARDCODED_ROLE = "superadmin"

# ------------------- FLASH CATEGORY MAPPING -------------------
flash_categories = {
    "error": "danger",
    "info": "info",
    "warning": "warning",
    "success": "success",
    "primary": "primary",
    "secondary": "secondary",
}


# ------------------- APP FACTORY -------------------
def create_app():
    app = Flask(
        __name__, 
        static_folder='main_app/static',
        template_folder='main_app/templates'
        # template_folder=os.path.join(os.path.abspath(os.path.dirname(__file__)), 'main_app', 'templates'),
        # static_folder=os.path.join(os.path.abspath(os.path.dirname(__file__)), 'main_app', 'static')
    )

    # ------------------- INSTANCE FOLDER & DATABASE CONFIG -------------------
    INSTANCE_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance')
    os.makedirs(INSTANCE_FOLDER, exist_ok=True)

    app.config['SECRET_KEY'] = 'supersecretkey'
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(INSTANCE_FOLDER, 'rakta_bandhan.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # ------------------- INITIALIZE EXTENSIONS -------------------
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = "info"

    # ------------------- CREATE TABLES -------------------
    with app.app_context():
        db.create_all()
        
        # =========================================
        # 🧠 AUTO-CREATE HARDCODED SUPERADMIN
        # =========================================
        existing_superadmin = User.query.filter_by(username=HARDCODED_USER).first()
        if not existing_superadmin:
            hashed_password = generate_password_hash(HARDCODED_PASS)
            new_superadmin = User(
                username=HARDCODED_USER,
                password=hashed_password,
                email=HARDCODED_EMAIL,
                phone=HARDCODED_PHONE,
                blood_grp=HARDCODED_BLOOD_GRP,
                address=HARDCODED_ADDRESS,
                role=HARDCODED_ROLE,
                profile_picture=HARDCODED_PROFILE_PIC,  # static path only
            )
            db.session.add(new_superadmin)
            db.session.commit()
            print(f"Superadmin '{HARDCODED_USER}' created successfully.")
        else:
            print("Superadmin already exists. Skipping creation.")
            
    # ------------------- USER LOADER -------------------
    @login_manager.user_loader
    def load_user(user_id):
        if not user_id or user_id == "None":
            return None
        try:
            return User.query.get(int(user_id))
        except ValueError:
            return None

    # ------------------- CONTEXT PROCESSORS -------------------
    @app.context_processor
    def inject_name():
        if current_user.is_authenticated:
            role = current_user.role.capitalize()
            return dict(name=f"{current_user.username} ({role})")
        return dict(name="")

    @app.context_processor
    def utility_processor():
        return dict(flash_categories=flash_categories)

    # ------------------- BLUEPRINTS -------------------
    from main_app.routes.user_routes import user_bp
    from main_app.routes.dashboard_routes import dashboard_bp
    from main_app.routes.auth_routes import auth_bp

    app.register_blueprint(user_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(auth_bp)

    return app

# ------------------- RUN THE APP -------------------
if __name__ == '__main__':
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
