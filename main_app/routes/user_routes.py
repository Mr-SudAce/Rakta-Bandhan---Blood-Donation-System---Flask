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
    return render_template("donor/profile.html")


@user_bp.route("/donate-blood", methods=["GET", "POST"])
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
            log_activity(f"New donation recorded for donor ID: {donor.id} on {new_donation.date}")
            db.session.add(new_donation)
            db.session.commit()
            log_activity(f"Added new donor: {donor.name} ({donor.blood_type})")

            flash(f"✅ Donation successfully registered for {name}! 🩸", "success")
            return redirect(url_for("user.home"))

        except Exception as e:
            db.session.rollback()
            flash(f"❌ Something went wrong: {e}", "danger")
            return redirect(url_for("user.donate_blood"))

    # ✅ Pre-fill form with user's data
    return render_template(
        "donor/donate_blood.html",
        user=current_user
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
        return redirect(url_for('campaign_detail', campaign_id=campaign.id))

    # Add new participant
    participant = Participant(user_id=current_user.id, campaign_id=campaign.id)
    log_activity(f"User ID: {current_user.id} joined campaign ID: {campaign.id}")
    db.session.add(participant)
    db.session.commit()

    flash("Successfully joined the campaign!", "success")
    return redirect(url_for('campaign_detail', campaign_id=campaign.id))



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