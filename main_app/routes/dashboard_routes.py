
from flask import Blueprint, app, render_template, redirect, url_for, request, flash, Response
from main_app.models import *
from io import StringIO
import csv
from main_app.helper_func.helperfunction import *
from flask_login import login_required, current_user

dashboard_bp = Blueprint('dashboard', __name__, template_folder='templates', static_folder='static', url_prefix='')

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role not in ["admin", "superadmin"]:
        return render_template("error/403.html"), 403

    
    total_capacity = BloodInventory.query.with_entities(db.func.sum(BloodInventory.quantity)).scalar() or 0
    donation_requests = Donor.query.count()
    
    if total_capacity == 0:
        inventoryStatus = "No Data"
        percent = 0
    elif donation_requests < 5:
        inventoryStatus = "Insufficient Data"
        percent = 0
    else:
        percent = (donation_requests / total_capacity) * 100

        if percent == 0:
            inventoryStatus = "Empty"
        elif percent <= 10:
            inventoryStatus = "Critical"
        elif percent <= 25:
            inventoryStatus = "Very Low"
        elif percent <= 50:
            inventoryStatus = "Low"
        elif percent <= 75:
            inventoryStatus = "Moderate"
        else:
            inventoryStatus = "Stable"
            
    totalDonor = donation_requests
    totalRecipient = User.query.filter_by(role='recipient').count()
    upcomingEvents = Campaign.query.count()
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
@dashboard_bp.route("/admin/events")
@login_required
def admin_events():
    if current_user.role not in ["admin", "superadmin"]:
        return render_template("error/403.html"), 403

    events = Campaign.query.all()
    participant_count = sum(len(event.participants) for event in events)
    return render_template("admin/events/manage_events.html", events=events, participant_count=participant_count)


# View one event
@dashboard_bp.route("/admin/events/<int:event_id>")
@login_required
def admin_event_detail(event_id):
    if current_user.role not in ["admin", "superadmin"]:
        return render_template("error/403.html"), 403
    
    event = Campaign.query.get_or_404(event_id)
    return redirect(url_for('user.campaign_detail', campaign_id=event.id))


# Edit an event
@dashboard_bp.route("/admin/events/edit/<int:event_id>", methods=["GET", "POST"])
@login_required
def admin_edit_event(event_id):
    if current_user.role not in ["admin", "superadmin"]:
        return render_template("error/403.html"), 403

    event = Campaign.query.get_or_404(event_id)
    
    participant_count = Participant.query.filter_by(campaign_id=event.id).count()

    if request.method == "POST":
        event.title = request.form["title"]
        event.date = request.form["date"]
        event.exp_date = request.form["exp_date"]
        event.location = request.form["location"]
        event.description = request.form["description"]
        event.participants_count = request.form.get("participants")
        event.camp_img = request.form.get("camp_img")

        # ✅ Convert date string (YYYY-MM-DD) → datetime.date
        date_str = request.form["date"]
        event.date = datetime.strptime(date_str, "%Y-%m-%d").date()
        event.exp_date = datetime.strptime(request.form["exp_date"], "%Y-%m-%d").date()
        
        log_activity(f"Event edited: {event.title} (ID: {event.id})")
        db.session.commit()
        flash("Event updated successfully!", "success")
        return redirect(url_for("dashboard.admin_events"))

    return render_template("admin/events/edit_event.html", event=event, participant_count=participant_count)

# Add a new event
@dashboard_bp.route("/campaigns/add_campaign", methods=["GET", "POST"])
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
        return redirect(url_for("user.campaigns"))  # or wherever you want

    return render_template("events/add-campaign.html")


# Delete an event
@dashboard_bp.route("/admin/events/delete/<int:event_id>")
@login_required
def admin_delete_event(event_id):
    if current_user.role not in ["admin", "superadmin"]:
        return render_template("error/403.html"), 403

    event = Campaign.query.get_or_404(event_id)
    # ✅ Log the deletion
    log_activity(f"Event deleted: {event.title} (ID: {event.id})")
    db.session.delete(event)
    db.session.commit()
    flash("Event deleted successfully!", "success")
    return redirect(url_for("dashboard.admin_events"))



# manage inventory
@dashboard_bp.route('/manage_inventory', methods=['GET', 'POST'])
def manage_inventory():
    inventory_data = BloodInventory.query.order_by(BloodInventory.blood_group).all()
    total_units = sum([item.quantity for item in inventory_data])

    return render_template(
        'admin/inventory/inventory.html',
        inventory=inventory_data,
        total_units=total_units
    )

# add inventory
@dashboard_bp.route('/add/inventory', methods=['GET', 'POST'])
def add_inventory():
    if request.method == 'POST':
        # Get form data
        blood_group = request.form.get('blood_group')
        component = request.form.get('component')
        quantity = request.form.get('quantity')
        collection_date = request.form.get('collection_date')
        expiry_date = request.form.get('expiry_date')

        # Basic validation
        if not blood_group or not component or not quantity or not collection_date or not expiry_date:
            flash("All fields are required.", "warning")
            return redirect(url_for('dashboard.add_inventory'))

        try:
            quantity = int(quantity)
            if quantity <= 0:
                flash("Quantity must be greater than 0.", "warning")
                return redirect(url_for('dashboard.add_inventory'))
        except ValueError:
            flash("Invalid quantity value.", "danger")
            return redirect(url_for('dashboard.add_inventory'))

        try:
            collection_date = datetime.strptime(collection_date, '%Y-%m-%d').date()
            expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()
        except ValueError:
            flash("Invalid date format. Use YYYY-MM-DD.", "danger")
            return redirect(url_for('dashboard.add_inventory'))
        
        
        existing_item = BloodInventory.query.filter_by(
            blood_group = blood_group,
            component = component
        ).first()
        
        if existing_item:
            existing_item.quantity += quantity
            existing_item.expiry_date = expiry_date
            db.session.commit()
        
        else:
            # Save new inventory record
            new_item = BloodInventory(
                blood_group=blood_group,
                component=component,
                quantity=quantity,
                collection_date=collection_date,
                expiry_date=expiry_date
            )
            db.session.add(new_item)
            db.session.commit()
            log_activity(f"Added new inventory: {blood_group} - {component}, Qty: {quantity}")
            flash("New blood inventory added successfully!", "success")
        return redirect(url_for('dashboard.manage_inventory'))
    return render_template('admin/inventory/add_inventory.html')

# sell inventory
@dashboard_bp.route('/sell/inventory/', methods=['GET', 'POST'])
def sell_inventory():
    if request.method == 'POST':
        blood_group = request.form.get('blood_group')
        component = request.form.get('component')
        quantity = int(request.form.get('quantity', 0))  # convert to int
        
          # Validate inputs
        if not blood_group or not component or not quantity:
            flash("All fields are required.", "warning")
            return redirect(url_for('dashboard.sell_inventory'))

        
        try:
            quantity = int(quantity)
            if quantity <= 0:
                flash("Quantity must be greater than 0.", "warning")
                return redirect(url_for('dashboard.sell_inventory'))
        except ValueError:
            flash("Invalid quantity value.", "danger")
            return redirect(url_for('dashboard.sell_inventory'))

        # Find inventory item
        inventory_item = BloodInventory.query.filter_by(
            blood_group=blood_group, component=component
        ).first()
        
        if not inventory_item:
            flash(f"No inventory found for {blood_group} ({component}).", "danger")
            return redirect(url_for('dashboard.sell_inventory'))
        
        
         # Check stock
        if inventory_item.quantity < quantity:
            flash(f"Not enough stock! Only {inventory_item.quantity} unit(s) available.", "danger")
            return redirect(url_for('dashboard.manage_inventory'))
        
        
        
        if inventory_item:
            # Deduct sold quantity
            inventory_item.quantity -= quantity
            new_quantity = inventory_item.quantity  # store new value

            # Delete if quantity is zero
            if new_quantity == 0:
                db.session.delete(inventory_item)

            db.session.commit()
            print(f"{inventory_item.component} ({inventory_item.blood_group}) new quantity: {new_quantity}")
        else:
            print(f"No inventory found for {blood_group} ({component})")
            
        
 

        return redirect(url_for('dashboard.manage_inventory'))

    # GET request — show form
    inventory_list = BloodInventory.query.all()
    return render_template('admin/inventory/blood_transaction.html', inventory=inventory_list)



# View reports
@dashboard_bp.route('/view_reports', methods=['GET'])
def view_reports():
    report_type = request.args.get('report_type')
    start_date = request.args.get('start_date')
    last_date = request.args.get('last_date')

    report_data = []
    report_headers = []
    title = "Reports"

    try:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d') if start_date else None
        last_date_obj = datetime.strptime(last_date, '%Y-%m-%d') if last_date else None
    except ValueError:
        start_date_obj = None
        last_date_obj = None

    # ==================== DONATION REPORT ====================
    if report_type == 'donations':
        title = "Donation Report"

        donation_query = DonationHistory.query.join(Donor, DonationHistory.donor_id == Donor.id)

        if start_date_obj:
            donation_query = donation_query.filter(DonationHistory.date >= start_date_obj)
        if last_date_obj:
            donation_query = donation_query.filter(DonationHistory.date <= last_date_obj)

        donation_list = donation_query.all()

        report_headers = ['Donor Name', 'Blood Type', 'Donation Date']
        for donation in donation_list:
            donor_name = donation.donor.name if donation.donor else 'N/A'
            blood_type = donation.donor.blood_type if donation.donor else 'N/A'
            donation_date = donation.date.strftime('%Y-%m-%d') if donation.date else 'N/A'
            report_data.append([donor_name, blood_type, donation_date])

    # ==================== INVENTORY REPORT ====================
    elif report_type == 'inventory':
        title = "Inventory Report"

        inventory_query = BloodInventory.query

        if start_date_obj:
            inventory_query = inventory_query.filter(BloodInventory.collection_date >= start_date_obj)
        if last_date_obj:
            inventory_query = inventory_query.filter(BloodInventory.collection_date <= last_date_obj)

        inventory_list = inventory_query.all()

        report_headers = ['Blood Group', 'Component', 'Quantity', 'Collection Date', 'Expiry Date']
        for item in inventory_list:
            report_data.append([
                item.blood_group,
                item.component,
                item.quantity,
                item.collection_date.strftime('%Y-%m-%d') if item.collection_date else 'N/A',
                item.expiry_date.strftime('%Y-%m-%d') if item.expiry_date else 'N/A'
            ])

    # ==================== CAMPAIGN REPORT ====================
    elif report_type == 'events':
        title = "Campaign Report"

        campaign_query = Campaign.query

        if start_date_obj:
            campaign_query = campaign_query.filter(Campaign.date >= start_date_obj)
        if last_date_obj:
            campaign_query = campaign_query.filter(Campaign.date <= last_date_obj)

        campaign_list = campaign_query.all()

        report_headers = ['Title', 'Location', 'Start Date', 'End Date', 'Organizer', 'Total Participants']
        for camp in campaign_list:
            participants_count = len(camp.participants) if camp.participants else 0
            report_data.append([
                camp.title,
                camp.location,
                camp.date.strftime('%Y-%m-%d') if camp.date else 'N/A',
                camp.exp_date.strftime('%Y-%m-%d') if camp.exp_date else 'N/A',
                camp.organizer or 'N/A',
                participants_count
            ])

    # ==================== UNKNOWN REPORT TYPE ====================
    else:
        title = "Reports"

    # Render the report
    return render_template(
        'admin/reports/reports.html',
        report_type=report_type,
        report_headers=report_headers,
        report_data=report_data,
        start_date=start_date_obj.strftime('%Y-%m-%d') if start_date_obj else "",
        last_date=last_date_obj.strftime('%Y-%m-%d') if last_date_obj else "",
        title=title
    )

# 📥 CSV Download Route
@dashboard_bp.route('/admin/download_report')
def admin_download_report():
    report_type = request.args.get('report_type')
    start_date = request.args.get('start_date')
    last_date = request.args.get('last_date')

    # Convert dates safely
    try:
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if last_date:
            last_date = datetime.strptime(last_date, '%Y-%m-%d')
    except ValueError:
        start_date = last_date = None

    report_headers = []
    report_data = []

    # ===== Donations Report =====
    if report_type == 'donations':
        query = DonationHistory.query
        if start_date:
            query = query.filter(DonationHistory.date >= start_date)
        if last_date:
            query = query.filter(DonationHistory.date <= last_date)
        results = query.all()

        report_headers = ['Donor Name', 'Blood Type', 'Date', 'Quantity']
        report_data = [
            [r.donor_name, r.blood_group, r.date.strftime('%Y-%m-%d'), r.quantity]
            for r in results
        ]

    # ===== Inventory Report =====
    elif report_type == 'inventory':
        query = BloodInventory.query
        if start_date:
            query = query.filter(BloodInventory.collection_date >= start_date)
        if last_date:
            query = query.filter(BloodInventory.collection_date <= last_date)
        results = query.all()

        report_headers = ['Blood Group', 'Component', 'Quantity', 'Collection Date']
        report_data = [
            [r.blood_group, r.component, r.quantity, r.collection_date.strftime('%Y-%m-%d')]
            for r in results
        ]

    # ===== Events Report =====
    elif report_type == 'events':
        query = Campaign.query
        if start_date:
            query = query.filter(Campaign.date >= start_date)
        if last_date:
            query = query.filter(Campaign.date <= last_date)
        results = query.all()

        report_headers = ['Event Name', 'Date', 'Location', 'Participants']
        report_data = [
            [r.event_name, r.date.strftime('%Y-%m-%d'), r.location, r.participants]
            for r in results
        ]

    # ===== Generate CSV =====
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(report_headers)
    cw.writerows(report_data)

    output = si.getvalue()
    si.close()

    return Response(
        output,
        mimetype='text/csv',
        headers={"Content-Disposition": f"attachment; filename={report_type}_report.csv"}
    )

if __name__ == '__main__':
    app.run(debug=True)