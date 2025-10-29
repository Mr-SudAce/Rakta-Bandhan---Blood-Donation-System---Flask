from app import app
from flask import render_template, redirect, url_for, request, flash
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



# @app.route("/admin/events")
# @login_required
# def admin_events_detail():
#     if current_user.role not in ["admin", "superadmin"]:
#         return render_template("error/403.html"), 403

#     events = Campaign.query.all()
#     return render_template("admin/events/events.html", events=events)


# @app.route("/admin/events/edit/<int:event_id>")
# @login_required
# def edit_admin_event_detail(event_id):
#     if current_user.role not in ["admin", "superadmin"]:
#         return render_template("error/403.html"), 403

#     event = Campaign.query.get_or_404(event_id)
#     return render_template("admin/events/event_detail.html", event=event)



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
