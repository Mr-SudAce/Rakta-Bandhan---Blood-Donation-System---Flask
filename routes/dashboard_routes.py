from app import app
from flask import render_template
from models import *
from flask_login import login_required, current_user

@app.route('/dashboard')
@login_required
def dashboard():

    if current_user.role not in ["admin", "superadmin"]:
        return render_template("error/403.html"), 403
    
    
    totalDonor = User.query.filter_by(role='donor').count()
    totalRecipient = User.query.filter_by(role='recipient').count()
    upcomingEvents = Campaign.query.count()
    inventoryStatus = "Stable"

    
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
