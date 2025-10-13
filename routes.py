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
        try:
            name = request.form.get("name").strip()
            phone = request.form.get("phone").strip()
            address = request.form.get("address").strip()
            blood_type = request.form.get("blood_type")
            DOB = request.form.get("DOB")
            gender = request.form.get("gender")
            email = request.form.get("email").strip()

            dob_date = datetime.strptime(DOB, '%Y-%m-%d').date() if DOB else None

            # ✅ Step 1: Get the current user's donor (if exists)
            existing_donor = Donor.query.filter_by(user_id=current_user.id).first()

            # ✅ Step 2: Check if the submitted data matches current_user
            data_changed = (
                name != current_user.username
                or email != current_user.email
                or (existing_donor and (
                    phone != existing_donor.phone or
                    address != existing_donor.address or
                    blood_type != existing_donor.blood_type or
                    gender != existing_donor.gender or
                    dob_date != existing_donor.DOB
                ))
            )

            # ✅ Step 3: If data changed → create a new donor record
            if data_changed or not existing_donor:
                donor = Donor(
                    user_id=current_user.id,
                    name=name,
                    email=email,
                    phone=phone,
                    address=address,
                    blood_type=blood_type,
                    DOB=dob_date,
                    gender=gender,
                    last_donation=datetime.utcnow().date()
                )
                db.session.add(donor)
                db.session.flush()
            else:
                donor = existing_donor
                donor.last_donation = datetime.utcnow().date()

            # ✅ Step 4: Record donation history
            new_donation = DonationHistory(
                donor_id=donor.id,
                request_id=0,
                date=datetime.utcnow().date()
            )
            db.session.add(new_donation)
            db.session.commit()

            flash(f"✅ Donation successfully registered for {name}! 🩸", "success")
            return redirect(url_for("home"))

        except Exception as e:
            db.session.rollback()
            flash(f"❌ Something went wrong: {e}", "danger")
            return redirect(url_for("donate_blood"))

    # ✅ Pre-fill form with user's data
    return render_template(
        "donor/donate_blood.html",
        user=current_user
    )


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
    # all donors data
    donation_data = Donor.query.all()
    
    # Extract unique addresses and blood types for dropdowns
    cities = sorted({donor.address for donor in donation_data if donor.address})
    groups = sorted({donor.blood_type for donor in donation_data if donor.blood_type})

    # Get search params
    selected_city = request.args.get("city")
    selected_group = request.args.get("group")
    
    # base query
    query = Donor.query
    
    # apply filters if selected
    if selected_city and selected_city != "Select":
        query = query.filter(Donor.address == selected_city)
    if selected_group and selected_group != "Select":
        query = query.filter(Donor.blood_type == selected_group)

    # Execute query and fetch results
    donation_data = query.all()

    return render_template(
        "recipient/find_blood.html",
        donors=donation_data,
        cities=cities,
        groups=groups,
        selected_city=selected_city,
        selected_group=selected_group
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

#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
# ==============================
# Authentication
# ==============================
@app.route("/login", methods=["GET", "POST"])
def login():
    try:
        if current_user.is_authenticated:
            return redirect(url_for("home"))

        form = LoginForm()

        if form.validate_on_submit():
            username = form.username.data.strip()
            password = form.password.data.strip()

            # 🚨 Check if any field is empty
            if not username or not password:
                flash("❌ Please fill out all fields.")
                return render_template("login.html", form=form)

            # Hardcoded Admin / Superadmin Login
            if username == HARDCODED_USER:
                # Validate admin credentials
                if password != HARDCODED_PASS:
                    flash("❌ Invalid Admin Password.")
                    return render_template("login.html", form=form)
                
                if not form.remember_me.data:
                    flash("❌ Remember Me option is not checked.")
                    return render_template("login.html", form=form)

                # Check if admin exists in DB
                user = User.query.filter_by(username=HARDCODED_USER).first()

                # Create hardcoded admin in DB if not found
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
                            role=HARDCODED_ROLE,
                        )
                        db.session.add(user)
                        db.session.commit()
                    except IntegrityError:
                        db.session.rollback()
                        user = User.query.filter_by(email=HARDCODED_EMAIL).first()
                    except Exception as e:
                        db.session.rollback()
                        flash(f"⚠️ Error creating admin user: {e}")
                        return render_template("login.html", form=form)

                login_user(user, remember=form.remember_me.data)
                flash("✅ Logged in as Superadmin!", "success")
                return redirect(url_for("home"))

            # Regular User Login
            try:
                user = User.query.filter_by(username=username).first()
            except Exception as e:
                flash(f"⚠️ Database error: {e}")
                return render_template("login.html", form=form)

            if not user:
                flash("❌ Username not found. Please register first.")
                return render_template("login.html", form=form)

            try:
                if not check_password_hash(user.password, password):
                    flash("❌ Incorrect password.")
                    return render_template("login.html", form=form)
            except Exception as e:
                flash(f"⚠️ Password check failed: {e}")
                return render_template("login.html", form=form)
            
            if not form.remember_me.data:
                flash("❌ Remember Me option is not checked.")
                return render_template("login.html", form=form)
            
            try:
                login_user(user)
                flash("✅ Login successful!", "success")
                return redirect(url_for("home"))
            except Exception as e:
                flash(f"⚠️ Login failed: {e}")
                return render_template("login.html", form=form)

        # GET request or invalid form submission
        return render_template("login.html", form=form)

    except Exception as e:
        flash(f"⚠️ Unexpected error: {e}")
        return render_template("login.html", form=LoginForm())






@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    try:
        if current_user.is_authenticated:
            return redirect(url_for("home"))

        form = RegisterForm()

        if form.validate_on_submit():
            try:
                # Check for duplicates
                if User.query.filter_by(username=form.username.data).first():
                    flash("❌ Username already exists.")
                    return redirect(url_for("register"))

                if User.query.filter_by(email=form.email.data).first():
                    flash("❌ Email already registered.")
                    return redirect(url_for("register"))

            except Exception as e:
                flash(f"⚠️ Database error while checking duplicates: {e}")
                return redirect(url_for("register"))

            try:
                hashed_password = generate_password_hash(form.password.data)
            except Exception as e:
                flash(f"⚠️ Password hashing failed: {e}")
                return render_template("register.html", form=form)

            try:
                filename = (
                    save_profile_picture(form.profile_picture.data)
                    if form.profile_picture.data
                    else "{{ url_for('static', filename='profile_pics/admin_dflt.jpg') }}"
                )
            except Exception as e:
                flash(f"⚠️ Profile picture upload failed: {e}")
                filename = "{{ url_for('static', filename='profile_pics/admin_dflt.jpg') }}"

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
                flash("⚠️ Registration failed. Please check your data.")
                return redirect(url_for("register"))
            except Exception as e:
                db.session.rollback()
                flash(f"⚠️ Unexpected error during registration: {e}")
                return redirect(url_for("register"))

            flash("✅ Registration successful. Please log in.")
            return redirect(url_for("login"))

        if form.errors:
            print("Form errors:", form.errors)  # Debugging
            flash("⚠️ Please fix the form errors and try again.")

        return render_template("register.html", form=form)

    except Exception as e:
        flash(f"⚠️ Unexpected error: {e}")
        return render_template("register.html", form=RegisterForm())

