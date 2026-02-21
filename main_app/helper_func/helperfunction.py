import os
from functools import wraps
from werkzeug.utils import secure_filename
from flask import current_app, redirect, url_for as reverse_url, flash
from slugify import slugify
from flask_login import current_user
from main_app.models import *
from datetime import datetime, date, timedelta
import random
import string

# Role-based access control decorator
def role_required(*roles):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.role not in roles:
                flash("Access denied!", "danger")
                return redirect(reverse_url('user.home'))
            return f(*args, **kwargs)
        return decorated_function
    return wrapper



# Save picture helper function
def save_picture(form_picture, foldername):
    # Define full folder path inside the static directory
    folder_path = os.path.join(current_app.root_path, "main_app/static/uploads/", foldername)
    os.makedirs(folder_path, exist_ok=True)

    filename = secure_filename(form_picture.filename)
    picture_path = os.path.join(folder_path, filename)

    # Save the actual image file to disk
    form_picture.save(picture_path)
    print(f"Saved picture to: {picture_path}")

    # ✅ Return relative path (browser-friendly)
    return f"{foldername}/{filename}"


def log_activity(action):
    """Add a new log entry for the current user."""
    user_id = current_user.id if current_user.is_authenticated else None
    activity = RecentActivity(user_id=user_id, action=action)
    db.session.add(activity)
    db.session.commit()
    return activity.id  # optional: return the log ID if needed

# ----------------------------
# Delete a specific log
# ----------------------------
def delete_log_activity(activity_id):
    """Delete a specific log entry by its ID."""
    activity = RecentActivity.query.get(activity_id)
    if activity:
        db.session.delete(activity)
        db.session.commit()
        return True
    return False

# ----------------------------
# Expire old logs automatically
# ----------------------------
def expire_log_activity(days_old=30):
    """
    Delete logs older than 'days_old' days.
    Default: logs older than 30 days.
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days_old)
    old_logs = RecentActivity.query.filter(RecentActivity.timestamp < cutoff_date).all()
    
    for log in old_logs:
        db.session.delete(log)
    
    db.session.commit()
    return len(old_logs)  # returns number of deleted logs


# Count Age
def count____age(user):
    today = date.today()
    dob = user.DOB

    year = today.year - dob.year
    month = today.month - dob.month
    day = today.day - dob.day

    # Fix day
    if day < 0:
        month -= 1
        last_month_date = today.replace(day=1) - timedelta(days=1)
        day += last_month_date.day

    # Fix month
    if month < 0:
        year -= 1
        month += 12

    return year, month, day

# Check eligibility
def check__eligibility(getUser_year):
    return getUser_year >= 18




# auto generation username
def generate_unique_username(fullname):
    base = slugify(fullname)
    base = "".join(char for char in base if char.isalnum()).lower()

    if not base:
        base = "user"

    while True:
        random_digits = "".join(random.choices(string.digits, k=4))
        username = f"{base}{random_digits}"

        existing = User.query.filter_by(username=username).first()
        if not existing:
            return username