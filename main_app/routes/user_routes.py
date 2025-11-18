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


@user_bp.route("/donate-blood", methods=["GET", "POST"])
@login_required
@role_required('donor')
def donate_blood():
    user = current_user

    # Age + eligibility from your helper functions
    age_year, age_month, age_day = count____age(user)
    eligibility = check__eligibility(age_year)

    if request.method == "POST":
        # Prevent bypassing the UI
        if not eligibility:
            flash("❌ You are not eligible to donate at the moment.", "danger")
            return redirect(url_for("user.donate_blood"))

        try:
            name = request.form.get("name").strip()
            phone = request.form.get("phone").strip()
            address = request.form.get("address").strip()
            blood_type = request.form.get("blood_type")
            DOB = request.form.get("DOB")
            gender = request.form.get("gender")
            email = request.form.get("email").strip()

            dob_date = datetime.strptime(DOB, '%Y-%m-%d').date() if DOB else None

            donor = Donor.query.filter_by(user_id=user.id).first()

            today = datetime.utcnow().date()

            # update donor
            if donor:
                donor.name = name
                donor.email = email
                donor.phone = phone
                donor.address = address
                donor.blood_type = blood_type
                donor.DOB = dob_date
                donor.gender = gender
                donor.last_donation = today
            else:
                donor = Donor(
                    user_id=user.id,
                    name=name,
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
                db.session.flush()

            new_donation = DonationHistory(
                donor_id=donor.id,
                request_id=0,
                date=today
            )
            db.session.add(new_donation)

            db.session.commit()
            flash("✅ Donation successfully registered!", "success")
            return redirect(url_for("user.home"))

        except Exception as e:
            db.session.rollback()
            flash(f"❌ Error: {e}", "danger")
            return redirect(url_for("user.donate_blood"))

    return render_template(
        "donor/donate_blood.html",
        eligibility=eligibility,
        age_year=age_year
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
    return render_template("donor/my_donation.html")

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
    
    # Check if user already joined
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