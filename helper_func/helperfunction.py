import os
from functools import wraps
from werkzeug.utils import secure_filename
from flask import current_app, redirect, url_for, flash
from flask_login import current_user


# Role-based access control decorator
def role_required(*roles):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.role not in roles:
                flash("Access denied!", "danger")
                return redirect(url_for("home"))
            return f(*args, **kwargs)
        return decorated_function
    return wrapper



# Save profile picture helper function
def save_profile_picture(form_picture):
    folder = os.path.join(current_app.root_path, "static/profile_pics")
    os.makedirs(folder, exist_ok=True)

    filename = secure_filename(form_picture.filename)
    picture_path = os.path.join(folder, filename)
    form_picture.save(picture_path)

    return filename