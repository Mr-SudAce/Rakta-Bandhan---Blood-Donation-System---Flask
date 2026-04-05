from flask import render_template, redirect, url_for, flash, request
from app import db
from main_app.models import *
from datetime import datetime
from flask_login import login_required, current_user
from datetime import *
from flask import Blueprint
from main_app.helper_func.helperfunction import *

user_bp = Blueprint('user', __name__, template_folder='templates', static_folder='static', url_prefix='')

# ==============================
# Root
# ==============================
@user_bp.route("/", endpoint='home')
@login_required
@role_required('donor', 'recipient')
def home():
    return render_template("home.html")


@user_bp.route("/contact")
@login_required
def contact():
    return render_template("contact.html")


# ==============================
# Common
# ==============================
@user_bp.route("/about")
@login_required
def about():
    return render_template("common/about.html")

@user_bp.route("/notifications")
@login_required
def notifications():
    return render_template("common/notifications.html")



# ==============================
# Donor
# ==============================
@user_bp.route("/profile")
@login_required
def profile():
    user = current_user  # or however you fetch your user

    age_year, age_month, age_day = count____age(user)
    eligibility = check__eligibility(age_year)

    return render_template(
        "donor/profile.html",
        age_year=age_year,
        age_month=age_month,
        age_day=age_day,
        eligibility=eligibility
    )


@user_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    user = db.session.get(User, current_user.id)
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        fullname = request.form.get("fullname", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()
        profile_picture = request.files.get("profile_picture")

        user.username = username
        user.full_name = fullname
        user.phone = phone
        user.address = address

        donor = Donor.query.filter_by(user_id=user.id).first()
        if donor:
            donor.name = fullname

        if profile_picture and profile_picture.filename != "":
            filename = save_picture(profile_picture, "profile_pics")
            user.profile_picture = filename

        try:
            db.session.commit()
            flash("✅ Profile updated successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"⚠️ Error updating profile: {str(e)}", "danger")

        return redirect(url_for("user.profile"))

    return render_template("donor/edit_profile.html", user=user)


@user_bp.route("/donate-blood", methods=["GET", "POST"])
@login_required
@role_required('donor')
def donate_blood():
    user = current_user

    age_year, age_month, age_day = count____age(user)
    eligibility = check__eligibility(age_year)

    if request.method == "POST":
        if not eligibility:
            flash("❌ You are not eligible to donate at the moment.", "danger")
            return redirect(url_for("user.donate_blood"))

        try:
            # Safely get form data and strip whitespace
            username = request.form.get("name", "").strip() or current_user.full_name
            phone = request.form.get("phone", "").strip() or current_user.phone
            address = request.form.get("address", "").strip() or current_user.address
            blood_type = request.form.get("blood_type") or current_user.blood_grp
            DOB = request.form.get("DOB")
            gender = request.form.get("gender") or current_user.gender
            email = request.form.get("email", "").strip() or current_user.email

            # Basic validation for required fields
            if not all([username, phone, address, blood_type, email]):
                flash("❌ Please fill out all required fields.", "danger")
                return redirect(url_for("user.donate_blood"))

            dob_date = datetime.strptime(DOB, '%Y-%m-%d').date() if DOB else user.DOB
            today = datetime.utcnow().date()

            # Find existing donor or prepare a new one
            donor = Donor.query.filter_by(user_id=user.id).first()

            # Check if donor has donated recently (90 days cooling period)
            if donor and donor.last_donation:
                days_since_donation = (today - donor.last_donation).days
                if days_since_donation < 90:
                    flash("❌ You have already donated. Please wait for the cooling period.", "danger")
                    return redirect(url_for("user.donate_blood"))

            if donor:
                # Update existing donor record
                donor.name = username
                donor.email = email
                donor.phone = phone
                donor.address = address
                donor.blood_type = blood_type
                donor.DOB = dob_date
                donor.gender = gender
                donor.last_donation = today
            else:
                # Create a new donor record
                donor = Donor(
                    user_id=user.id,
                    name=username,
                    email=email,
                    phone=phone,
                    address=address,
                    blood_type=blood_type,
                    DOB=dob_date,
                    gender=gender,
                    last_donation=today,
                    is_active=True
                )
                db.session.add(donor)
                # Flush to get the new donor's ID for the history record
                db.session.flush()

            # Create a history record for this donation
            new_donation = DonationHistory(
                donor_id=donor.id,
                request_id=0,  # Assuming 0 is a placeholder for direct donations
                date=today
            )
            db.session.add(new_donation)

            # Commit all changes to the database
            db.session.commit()
            log_activity(f"User '{user.username}' registered a donation.")
            flash("✅ Donation successfully registered! Thank you for being a hero.", "success")
            return redirect(url_for("user.home"))

        except Exception as e:
            db.session.rollback()
            flash(f"❌ An unexpected error occurred: {e}", "danger")
            return redirect(url_for("user.donate_blood"))

    # For GET request, you might want to pass existing donor info to pre-fill the form
    donor = Donor.query.filter_by(user_id=user.id).first()

    return render_template(
        "donor/donate_blood.html",
        eligibility=eligibility,
        age_year=age_year,
        donor=donor
    )


@user_bp.route("/donor/register-event")
@login_required
@role_required('donor')
def donor_register_event():
    return render_template("donor/register_event.html")


@user_bp.route("/my-donation")
@login_required
@role_required('donor')
def my_donations():
    today = date.today()
    donations = (
        db.session.query(Campaign)
        .join(Participant, Participant.campaign_id == Campaign.id)
        .filter(Participant.user_id == current_user.id)
        .filter(Campaign.date < today)
        .order_by(Campaign.date.desc())
        .all()
    )
    return render_template("donor/my_donation.html", donations=donations)

# ==============================
# Campaigns
# ==============================

@user_bp.route("/campaigns")
def campaigns():
    paginations = request.args.get('page', 1, type=int)
    all_campaigns = Campaign.query.order_by(Campaign.date.asc()).paginate(page=paginations, per_page=9)
    return render_template("events/campaign.html", campaigns=all_campaigns, paginations=paginations)

# campaign detail route
@user_bp.route('/campaign/<int:campaign_id>')
def campaign_detail(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    return render_template('events/campaign_detail.html', campaign=campaign)

@user_bp.route('/campaign/<int:campaign_id>/join', methods=['POST', 'GET'])
@login_required
def join_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    existing = Participant.query.filter_by(user_id=current_user.id, campaign_id=campaign.id).first()
    if existing:
        flash("You've already joined this campaign!", "warning")
        return redirect(url_for('user.campaign_detail', campaign_id=campaign.id))

    # Add new participant
    participant = Participant(user_id=current_user.id, campaign_id=campaign.id)
    log_activity(f"User ID: {current_user.id} joined campaign ID: {campaign.id}")
    db.session.add(participant)
    db.session.commit()

    flash("Successfully joined the campaign!", "success")
    return redirect(url_for('user.campaign_detail', campaign_id=campaign.id))



# ==============================
# Recipient
# ==============================
@user_bp.route("/recipient/dashboard")
@login_required
@role_required('recipient')
def recipient_dashboard():
    donor_data = Donor.query.all()
    total_requests = len(donor_data)
    return render_template("recipient/dashboard.html", donor_data=donor_data, total_requests=total_requests)


@user_bp.route("/recipient/requests")
@login_required
@role_required('recipient')
def recipient_requests():
    return render_template("recipient/requests.html")


@user_bp.route("/find-blood", methods=["GET"])
@login_required
def find_blood():
    # all donors data
    donation_data = Donor.query.all()
    
    # Extract unique addresses and blood types for dropdowns
    cities = sorted({donor.address for donor in donation_data if donor.address})
    groups = sorted({donor.blood_type for donor in donation_data if donor.blood_type})

    # Get search params
    selected_city = request.args.get("blood_type")
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




@user_bp.route("/requests")
@login_required
def my_requests():
    return render_template("recipient/requests.html")


# ==============================
# Events
# ==============================
@user_bp.route("/events")
@login_required
def events():
    return render_template("events/events.html")