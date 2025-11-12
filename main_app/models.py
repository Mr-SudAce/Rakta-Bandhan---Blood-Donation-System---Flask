from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from extensions import db


class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False, unique=True)
    blood_grp = db.Column(db.String(5), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    DOB = db.Column(db.Date, nullable=False, default=datetime(1900, 1, 1))
    gender = db.Column(db.String(10), nullable=False, default='None')
    profile_picture = db.Column(db.String(200), default='static_images/default.jpg')
    role = db.Column(db.String(20), nullable=False)

    # one-to-one relationship with Donor
    donor = db.relationship('Donor', backref='user', uselist=False)
    
    # one-to-many relationship with BloodRequest
    requests = db.relationship('BloodRequest', backref='recipient', lazy=True)

class Donor(db.Model):
    __tablename__ = "donors"
    __table_args__ = (
        db.UniqueConstraint('user_id', name='unique_user_donor'),
        db.CheckConstraint(
            "blood_type IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')",
            name='valid_blood_type'
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    blood_type = db.Column(db.String(5), nullable=False)
    address = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    DOB = db.Column(db.Date)
    gender = db.Column(db.String(10))
    email = db.Column(db.String(120))
    last_donation = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)  # optional but useful for deactivating donors

    # Relationship with DonationHistory
    donations = db.relationship('DonationHistory', backref='donor', lazy=True)

    def __repr__(self):
        return f"<Donor {self.name} ({self.blood_type})>"
    
    

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
    camp_img = db.Column(db.String(255), nullable=True)
    location = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    exp_date = db.Column(db.Date, nullable=False)
    organizer = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    participants = db.relationship(
        "Participant",
        back_populates="campaign",
        lazy=True,
        cascade="all, delete-orphan"
    )

class Participant(db.Model): 
    __tablename__ = 'participants'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'), nullable=True)
    campaign = db.relationship(
        "Campaign",
        back_populates="participants"
    )
    
    

class RecentActivity(db.Model):
    __tablename__ = "recent_activities"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Activity {self.action}>"
    

class BloodInventory(db.Model):
    __tablename__ = 'blood_inventory'
    id = db.Column(db.Integer, primary_key=True)
    blood_group = db.Column(db.String(5), nullable=False)
    component = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, default=0)
    collection_date = db.Column(db.Date, nullable=False)
    expiry_date = db.Column(db.Date, nullable=False)

    def __repr__(self):
        return f"<BloodInventory {self.blood_group} ({self.component})>"