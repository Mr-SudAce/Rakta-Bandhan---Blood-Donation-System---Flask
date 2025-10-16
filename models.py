from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin




db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False, unique=True)
    blood_grp = db.Column(db.String(5), nullable=False)
    address = db.Column(db.String(200), nullable=False) 
    profile_picture = db.Column(db.String(200), default='profile_pics/default.jpg')
    role = db.Column(db.String(20), nullable=False)

    # one-to-one relationship with Donor
    donor = db.relationship('Donor', backref='user', uselist=False)
    
    # one-to-many relationship with BloodRequest
    requests = db.relationship('BloodRequest', backref='recipient', lazy=True)

class Donor(db.Model):
    __tablename__ = "donors"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    blood_type = db.Column(db.String(5), nullable=False)
    address = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    DOB = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    last_donation = db.Column(db.Date, nullable=True)
    donations = db.relationship('DonationHistory', backref='donor', lazy=True)

class BloodRequest(db.Model):
    __tablename__ = "blood_requests"
    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    blood_type = db.Column(db.String(5), nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)
    histories = db.relationship('DonationHistory', backref='request', lazy=True)

class DonationHistory(db.Model):
    __tablename__ = "donation_history"
    id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.Integer, db.ForeignKey('donors.id'), nullable=False)
    request_id = db.Column(db.Integer, db.ForeignKey('blood_requests.id'), nullable=True)
    date = db.Column(db.Date, nullable=False)
    


class Campaign(db.Model):
    __tablename__ = "campaigns"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    organizer = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(255), nullable=True)