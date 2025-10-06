from flask_wtf import FlaskForm
from wtforms import *
from wtforms.validators import *
from flask_wtf.file import FileField, FileAllowed

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")
    remember_me = BooleanField("Remember Me")


class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    phone = StringField("Phone", validators=[DataRequired(), Length(min=7, max=20)])
    blood_grp = SelectField(
        "Blood Group",
        choices=[
            ("A+", "A+"),
            ("A-", "A-"),
            ("B+", "B+"),
            ("B-", "B-"),
            ("O+", "O+"),
            ("O-", "O-"),
            ("AB+", "AB+"),
            ("AB-", "AB-"),
        ],
        validators=[DataRequired()],
    )
    address = StringField(
        "Address", validators=[DataRequired(), Length(min=5, max=200)]
    )
    profile_picture = FileField(
        "Profile Picture",
        validators=[FileAllowed(["jpg", "jpeg", "png"], "Images only!")],
    )
    role = SelectField("Role", choices=[("donor", "Donor"), ("recipient", "Recipient")])
    submit = SubmitField("Register")


class DonorForm(FlaskForm):
    blood_type = SelectField(
        "Blood Type",
        choices=[
            ("A+", "A+"),
            ("A-", "A-"),
            ("B+", "B+"),
            ("B-", "B-"),
            ("O+", "O+"),
            ("O-", "O-"),
            ("AB+", "AB+"),
            ("AB-", "AB-"),
        ],
    )
    last_donation = DateField("Last Donation")
    submit = SubmitField("Update")


class RequestForm(FlaskForm):
    blood_type = SelectField(
        "Blood Type",
        choices=[
            ("A+", "A+"),
            ("A-", "A-"),
            ("B+", "B+"),
            ("B-", "B-"),
            ("O+", "O+"),
            ("O-", "O-"),
            ("AB+", "AB+"),
            ("AB-", "AB-"),
        ],
    )
    submit = SubmitField("Request")


class SearchForm(FlaskForm):
    blood_type = SelectField(
        "Blood Type",
        choices=[
            ("A+", "A+"),
            ("A-", "A-"),
            ("B+", "B+"),
            ("B-", "B-"),
            ("O+", "O+"),
            ("O-", "O-"),
            ("AB+", "AB+"),
            ("AB-", "AB-"),
        ],
    )
    submit = SubmitField("Search")
