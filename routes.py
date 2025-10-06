from flask import render_template, redirect, url_for, flash, request
from app import app, db
from models import *
from forms import RegisterForm, LoginForm
from sqlalchemy.exc import IntegrityError
from flask_login import login_user, logout_user, login_required, current_user
from models import User
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import *
from app import HARDCODED_USER, HARDCODED_PASS, HARDCODED_EMAIL, HARDCODED_PHONE, HARDCODED_BLOOD_GRP, HARDCODED_ADDRESS, HARDCODED_PROFILE_PIC, HARDCODED_ROLE
from helper_func.helperfunction import *


# ==============================
# Root
# ==============================
@app.route("/")
@login_required
def home():
    return render_template("home.html")


@app.route("/contact")
@login_required
def contact():
    return render_template("contact.html")


# ==============================
# Common
# ==============================
@app.route("/about")
@login_required
def about():
    return render_template("common/about.html")


# ==============================
# Donor
# ==============================
@app.route("/profile")
@login_required
def profile():
    return render_template("donor/profile.html")


@app.route("/donate-blood", methods=["GET", "POST"])
@login_required
@role_required('donor')
def donate_blood():
    if request.method == "POST":
        # Get form data
        name = request.form.get("name")
        phone = request.form.get("phone")
        address = request.form.get("address")
        blood_type = request.form.get("blood_type")
        age = request.form.get("age")
        DOB = request.form.get("DOB")
        gender = request.form.get("gender")
        email = request.form.get("email")

        # Create donor entry
        new_donor = Donor(
            user_id=current_user.id,
            name=name or current_user.name,  # fallback to user's name
            email=email or current_user.email,  # fallback to user's email
            phone=phone,
            address=address,
            blood_type=blood_type,
            age=age if age else None,
            DOB=DOB if DOB else None,
            gender=gender
        )

        db.session.add(new_donor)
        db.session.commit()

        flash("🎉 Thank you for registering as a donor!", "success")
        return redirect(url_for("home"))

    return render_template("donor/donate_blood.html")


@app.route("/donor/register-event")
@login_required
@role_required('donor')
def donor_register_event():
    return render_template("donor/register_event.html")


@app.route("/my-donation")
@login_required
@role_required('donor')
def my_donations():
    return render_template("donor/my_donation.html")


# ==============================
# Recipient
# ==============================
@app.route("/recipient/dashboard")
@login_required
@role_required('recipient')
def recipient_dashboard():
    donor_data = Donor.query.all()
    total_requests = len(donor_data)
    return render_template("recipient/dashboard.html", donor_data=donor_data, total_requests=total_requests)


@app.route("/recipient/requests")
@login_required
@role_required('recipient')
def recipient_requests():
    return render_template("recipient/requests.html")


@app.route("/find-blood", methods=["GET"])
@login_required
def find_blood():
    donordata = Donor.query.all()
    city = request.args.get("q")
    group = request.args.get("group")
    urgency = request.args.get("urgency")

    filtered_donors = []

    if city or group or urgency:
        for donor in donordata:
            if city and donor.city.lower() != city.lower():
                continue
            if group and donor.group != group:
                continue
            if urgency and donor.urgency != urgency:
                continue
            filtered_donors.append(donor)

    return render_template(
        "recipient/find_blood.html",
        donors=filtered_donors,
        city=city,
        group=group,
        urgency=urgency
    )


@app.route("/requests")
@login_required
def my_requests():
    return render_template("recipient/requests.html")


# ==============================
# Events
# ==============================
@app.route("/events")
@login_required
def events():
    return render_template("events/events.html")


# ==============================
# Authentication
# ==============================
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data.strip()
        password = form.password.data.strip()

        # 🚨 Empty field check
        if not username or not password:
            flash("❌ Username and password cannot be empty", "danger")
            return render_template("login.html", form=form)

        # 🧠 Check if user matches the hardcoded credentials first
        if username == HARDCODED_USER and password == HARDCODED_PASS:
            # Ensure the hardcoded user exists in DB
            user = User.query.filter_by(username=HARDCODED_USER).first()

            if not user:
                try:
                    user = User(
                        username=HARDCODED_USER,
                        password=generate_password_hash(HARDCODED_PASS),
                        email=HARDCODED_EMAIL,
                        phone=HARDCODED_PHONE,
                        blood_grp=HARDCODED_BLOOD_GRP,
                        address=HARDCODED_ADDRESS,
                        profile_picture=HARDCODED_PROFILE_PIC,
                        role=HARDCODED_ROLE
                    )
                    db.session.add(user)
                    db.session.commit()
                except IntegrityError:
                    db.session.rollback()
                    user = User.query.filter_by(email=HARDCODED_EMAIL).first()

            login_user(user, remember=form.remember_me.data)
            flash("✅ Logged in as admin!", "success")
            return redirect(url_for("home"))

        # 🧍‍♂️ Regular user login
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user, remember=form.remember_me.data)
            flash("✅ Login successful", "success")
            return redirect(url_for("home"))
        else:
            flash("❌ Invalid username or password", "danger")
            return render_template("login.html", form=form)

    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    form = RegisterForm()

    if form.validate_on_submit():
        # Check for duplicates
        if User.query.filter_by(username=form.username.data).first():
            flash("Username already exists.")
            return redirect(url_for("register"))

        if User.query.filter_by(email=form.email.data).first():
            flash("Email already registered.")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(form.password.data)
        filename = save_profile_picture(form.profile_picture.data) if form.profile_picture.data else "{{ url_for('static', filename='profile_pics/admin_dflt.jpg') }}"

        user = User(
            username=form.username.data,
            password=hashed_password,
            email=form.email.data,
            phone=form.phone.data,
            blood_grp=form.blood_grp.data,
            address=form.address.data,
            profile_picture=filename,
            role=form.role.data,
        )

        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Registration failed. Please check your data.")
            return redirect(url_for("register"))

        flash("Registration successful. Please log in.")
        return redirect(url_for("login"))

    if form.errors:
        print("Form errors:", form.errors)  # Debugging

    return render_template("register.html", form=form)


