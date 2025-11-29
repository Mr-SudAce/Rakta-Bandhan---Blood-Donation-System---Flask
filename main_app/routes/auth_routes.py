from flask import Blueprint, render_template, redirect, session, url_for, flash
from main_app.models import *
from main_app.forms import RegisterForm, LoginForm
from sqlalchemy.exc import IntegrityError
from main_app.helper_func.helperfunction import * 
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from app import HARDCODED_USER, HARDCODED_PASS


auth_bp = Blueprint('auth', __name__, template_folder='templates/auth', static_folder='static/auth', url_prefix='')
# ==============================
# Authentication
# ==============================
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    try:
        # Redirect if already logged in
        if current_user.is_authenticated:
            return redirect(url_for("user.home"))

        form = LoginForm()

        if form.validate_on_submit():
            username = form.username.data.strip()
            password = form.password.data.strip()


            if any(char.isdigit() for char in username):
                flash('🚫 Username cannot contain numbers.')
                return render_template('register.html', form=form)
            
            # Empty fields check
            if not username or not password:
                flash("❌ Please fill out all fields.", "error")
                return render_template("login.html", form=form)

            # =========================================
            # --- HARDCODED LOGIN CHECK ---
            # =========================================
            if username == HARDCODED_USER and password == HARDCODED_PASS:
                user = User.query.filter_by(username=HARDCODED_USER).first()
                if user:
                    login_user(user, remember=False)
                    # 🔥 Auto logout timer here
                    session.permanent = True
                    session["last_active"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

                    flash(f"✅ Logged in successfully as {user.role.capitalize()}!", "success")
                    return redirect(url_for("dashboard.dashboard"))

            # --- Database login ---
            user = User.query.filter_by(username=username).first()
            if not user:
                flash("❌ Username not found. Please register first.", "error")
                return render_template("login.html", form=form)

            if not check_password_hash(user.password, password):
                flash("❌ Incorrect password.", "error")
                return render_template("login.html", form=form)
            
            

            login_user(user, remember=False)

            session.permanent = True
            session["last_active"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

            flash(f"✅ Logged in successfully as {user.role.capitalize()}!", "success")
            return redirect(url_for("user.home"))

        return render_template("login.html", form=form)

    except Exception as e:
        flash(f"⚠️ Unexpected error: {e}", "error")
        return render_template("login.html", form=form)



@auth_bp.route("/logout")
@login_required
def logout():
    log_activity(f"User ID: {current_user.id} {current_user.username} logged out.")
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for("auth.login"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    try:
        if current_user.is_authenticated:
            return redirect(url_for("user.home"))

        form = RegisterForm()

        if form.validate_on_submit():
            try:
                # Check for duplicates
                if User.query.filter_by(username=form.username.data).first():
                    flash("❌ Username already exists.")
                    return redirect(url_for("auth.register"))

                if User.query.filter_by(email=form.email.data).first():
                    flash("❌ Email already registered.")
                    return redirect(url_for("auth.register"))
                
                if not form.email.data.endswith("@gmail.com"):
                    flash("❌ Only Gmail addresses are allowed.")
                    return redirect(url_for("auth.register"))

                if User.query.filter_by(phone=form.phone.data).first():
                    flash("❌ Phone number already registered.")
                    return redirect(url_for("auth.register"))
                
                if any(char.isdigit() for char in form.username.data):
                    flash('🚫 Username cannot contain numbers.')
                    return render_template('register.html', form=form)

            except Exception as e:
                flash(f"⚠️ Database error while checking duplicates: {e}")
                return redirect(url_for("auth.register"))

            try:
                hashed_password = generate_password_hash(form.password.data)
            except Exception as e:
                flash(f"⚠️ Password hashing failed: {e}")
                return render_template("register.html", form=form)

            try:
                if form.profile_picture.data:
                    filename = save_picture(form.profile_picture.data, "profile_pics")
                else:
                    filename = "static_images/default.png"
            except Exception as e:
                flash(f"⚠️ Profile picture upload failed: {e}")
                filename = "static_images/default.png"

            user = User(
                username=form.username.data,
                password=hashed_password,
                email=form.email.data,
                phone=form.phone.data,
                blood_grp=form.blood_grp.data,
                DOB=form.DOB.data,
                gender=form.gender.data,
                address=form.address.data,
                profile_picture=filename,
                role=form.role.data,
            )
            try:
                db.session.add(user)
                db.session.commit()
                log_activity(f"New user registered: {user.username} ({user.role})")
            except IntegrityError:
                db.session.rollback()
                flash("⚠️ Registration failed. Please check your data.")
                return redirect(url_for("auth.register"))
            except Exception as e:
                db.session.rollback()
                flash(f"⚠️ Unexpected error during registration: {e}")
                return redirect(url_for("auth.register"))

            flash("✅ Registration successful. Please log in.")
            return redirect(url_for("auth.login"))

        if form.errors:
            print("Form errors:", form.errors)  # Debugging
            flash("⚠️ Please fix the form errors and try again.")

        return render_template("register.html", form=form)

    except Exception as e:
        flash(f"⚠️ Unexpected error: {e}")
        return render_template("register.html", form=RegisterForm())

