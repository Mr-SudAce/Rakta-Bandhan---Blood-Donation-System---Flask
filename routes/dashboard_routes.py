from app import app
from flask import render_template, redirect, url_for, request, flash
from models import *
from helper_func.helperfunction import * 
from flask_login import login_required, current_user
# from sqlalchemy import func

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role not in ["admin", "superadmin"]:
        return render_template("error/403.html"), 403

    donation_requests = User.query.filter(User.role == "donor").count()
       
    if donation_requests == 0:
        inventoryStatus = "Critical"
    elif 1 <= donation_requests <= 10:
        inventoryStatus = "Very Low"
    elif 11 <= donation_requests <= 25:
        inventoryStatus = "Low"
    elif 26 <= donation_requests <= 50:
        inventoryStatus = "Moderate"
    else:
        inventoryStatus = "Stable"
        
    totalDonor = User.query.filter_by(role='donor').count()
    totalRecipient = User.query.filter_by(role='recipient').count()
    upcomingEvents = Campaign.query.count()
    # Recent activities
    recent_activities = RecentActivity.query.order_by(RecentActivity.timestamp.desc()).limit(10).all()

    return render_template(
        'admin/dashboard.html',
        current_user=current_user,
        is_superadmin=(current_user.username == "superadmin"),
        total_donors=totalDonor,
        total_recipients=totalRecipient,
        upcoming_events=upcomingEvents,
        inventory_status=inventoryStatus,
        recent_activities=recent_activities
    )


# View all events
@app.route("/admin/events")
@login_required
def admin_events():
    if current_user.role not in ["admin", "superadmin"]:
        return render_template("error/403.html"), 403

    events = Campaign.query.all()
    participant_count = sum(len(event.participants) for event in events)
    return render_template("admin/events/manage_events.html", events=events, participant_count=participant_count)


# View one event
@app.route("/admin/events/<int:event_id>")
@login_required
def admin_event_detail(event_id):
    if current_user.role not in ["admin", "superadmin"]:
        return render_template("error/403.html"), 403

    event = Campaign.query.get_or_404(event_id)
    return render_template("admin/events/event_detail.html", event=event)


# Edit an event
@app.route("/admin/events/edit/<int:event_id>", methods=["GET", "POST"])
@login_required
def admin_edit_event(event_id):
    if current_user.role not in ["admin", "superadmin"]:
        return render_template("error/403.html"), 403

    event = Campaign.query.get_or_404(event_id)
    
    participant_count = Participant.query.filter_by(campaign_id=event.id).count()

    if request.method == "POST":
        event.title = request.form["title"]
        event.date = request.form["date"]
        event.location = request.form["location"]
        event.description = request.form["description"]
        event.participants_count = request.form.get("participants")

        # ✅ Convert date string (YYYY-MM-DD) → datetime.date
        date_str = request.form["date"]
        event.date = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        
        db.session.commit()
        flash("Event updated successfully!", "success")
        return redirect(url_for("admin_events"))

    return render_template("admin/events/edit_event.html", event=event, participant_count=participant_count)

# Add a new event
@app.route("/campaigns/add_campaign", methods=["GET", "POST"])
def add_campaign():
    if request.method == "POST":
        title = request.form.get("title")
        location = request.form.get("location")
        date = request.form.get("date")
        exp_date = request.form.get("exp_date")
        organizer = request.form.get("organizer")
        description = request.form.get("description")
        
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
        exp_date_obj = datetime.strptime(exp_date, "%Y-%m-%d").date()

        # Handle image file upload
        image_file = request.files.get("camp_img")
        camp_img = None

        if image_file and image_file.filename != "":
            camp_img = save_picture(image_file, "campaigns")

        new_campaign = Campaign(
            title=title,
            location=location,
            date=date_obj,
            exp_date=exp_date_obj,  
            organizer=organizer,
            description=description,
            camp_img=camp_img
        )

        db.session.add(new_campaign)
        db.session.commit()

        log_activity(f"Campaign added: {title}")
        flash("Campaign added successfully!", "success")
        return redirect(url_for("campaigns"))  # or wherever you want

    return render_template("events/add-campaign.html")



# Delete an event
@app.route("/admin/events/delete/<int:event_id>")
@login_required
def admin_delete_event(event_id):
    if current_user.role not in ["admin", "superadmin"]:
        return render_template("error/403.html"), 403

    event = Campaign.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    flash("Event deleted successfully!", "success")
    return redirect(url_for("admin_events"))



# manage inventory

@app.route('/manage_inventory', methods=['GET', 'POST'])
def manage_inventory():
    if request.method == 'POST':
        # Get form data
        blood_group = request.form.get('blood_group')
        component = request.form.get('component')
        quantity = int(request.form.get('quantity', 0))
        collection_date = request.form.get('collection_date')
        expiry_date = request.form.get('expiry_date')

        # Convert dates from string to date objects
        try:
            collection_date = datetime.strptime(collection_date, '%Y-%m-%d').date()
            expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()
        except ValueError:
            flash("Invalid date format. Use YYYY-MM-DD.", "danger")
            return redirect(url_for('manage_inventory'))

        # Create new inventory entry
        new_item = BloodInventory(
            blood_group=blood_group,
            component=component,
            quantity=quantity,
            collection_date=collection_date,
            expiry_date=expiry_date
        )
        db.session.add(new_item)
        db.session.commit()
        flash("New blood inventory added successfully!", "success")
        return redirect(url_for('manage_inventory'))

    # GET request — show inventory
    inventory_data = BloodInventory.query.order_by(BloodInventory.blood_group).all()
    total_units = sum([item.quantity for item in inventory_data])
    
    critical_units = [item for item in inventory_data if item.quantity < 5]
    low_units = [item for item in inventory_data if 5 <= item.quantity < 15]
    stable_units = [item for item in inventory_data if item.quantity >= 15]

    inventory_status = "Critical" if len(critical_units) > 0 else (
        "Low" if len(low_units) > 0 else "Stable"
    )

    return render_template(
        'admin/inventory/inventory.html',
        inventory=inventory_data,
        total_units=total_units,
        inventory_status=inventory_status
    )

@app.route('/add/inventory', methods=['GET', 'POST'])
def add_inventory():
    if request.method == 'POST':
        blood_group = request.form['blood_group']
        quantity = int(request.form['quantity'])
        
        new_inventory = BloodInventory(blood_group=blood_group, quantity=quantity)
        db.session.add(new_inventory)
        db.session.commit()
        
        flash('Inventory added successfully!', 'success')
        return redirect(url_for('manage_inventory'))
    return render_template('admin/inventory/add_inventory.html')
    

# View reports
@app.route('/view_reports')
def view_reports():
    
    return render_template(
        'admin/reports/reports.html'
    )