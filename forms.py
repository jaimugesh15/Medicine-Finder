"""Flask-WTF forms (server-side validation + CSRF)."""
from flask_wtf import FlaskForm
from wtforms import (BooleanField, FloatField, IntegerField, PasswordField, SelectField,
                     StringField, TextAreaField)
from wtforms.validators import (DataRequired, EqualTo, Length, NumberRange, Optional,
                                Regexp)

EMAIL_RE = r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$"
PHONE_RE = r"^\+?[\d\s\-()]{7,18}$"

CATEGORIES = ["Pain & fever", "Cold & allergy", "Antibiotics", "Diabetes care",
              "Heart & blood pressure", "Digestive health", "Vitamins & supplements",
              "First aid & supplies", "Other"]
FORMS = ["Tablet", "Capsule", "Syrup", "Injection", "Ointment / cream", "Drops",
         "Sachet / powder", "Inhaler", "Other"]


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Regexp(EMAIL_RE, message="Enter a valid email address.")])
    password = PasswordField("Password", validators=[DataRequired()])


class RegisterForm(FlaskForm):
    full_name = StringField("Your name", validators=[DataRequired(), Length(max=100)])
    pharmacy_name = StringField("Pharmacy name", validators=[DataRequired(), Length(max=120)])
    city = StringField("City", validators=[DataRequired(), Length(max=80)])
    email = StringField("Email", validators=[DataRequired(), Length(max=120),
                                              Regexp(EMAIL_RE, message="Enter a valid email address.")])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=72, message="Use 8 to 72 characters.")])
    confirm = PasswordField("Confirm password", validators=[DataRequired(), EqualTo("password", message="Passwords do not match.")])


class MedicineForm(FlaskForm):
    name = StringField("Medicine name", validators=[DataRequired(), Length(max=120)])
    category = SelectField("Category", choices=[(c, c) for c in CATEGORIES])
    strength = StringField("Strength", validators=[Length(max=40)], description="For example 500 mg")
    dosage_form = SelectField("Dosage form", choices=[("", "Not applicable")] + [(f, f) for f in FORMS])
    manufacturer = StringField("Manufacturer", validators=[Optional(), Length(max=100)])
    quantity = IntegerField("Stock quantity", validators=[NumberRange(min=0, max=1000000, message="Quantity cannot be negative.")])
    reorder_level = IntegerField("Reorder level", validators=[NumberRange(min=0, max=1000000, message="Reorder level cannot be negative.")], default=10)
    verified = BooleanField("I have counted this stock (verified)")
    notes = TextAreaField("Notes", validators=[Optional(), Length(max=500)])


class ProfileForm(FlaskForm):
    name = StringField("Pharmacy name", validators=[DataRequired(), Length(max=120)])
    manager_name = StringField("Owner / manager name", validators=[DataRequired(), Length(max=100)])
    phone = StringField("Contact number", validators=[DataRequired(), Regexp(PHONE_RE, message="Enter a valid phone number.")])
    email = StringField("Email address", validators=[Optional(), Regexp(EMAIL_RE, message="Enter a valid email address.")])
    address = StringField("Full address", validators=[DataRequired(), Length(max=200)])
    city = StringField("City", validators=[DataRequired(), Length(max=80)])
    postal_code = StringField("Postal code", validators=[Optional(), Regexp(r"^[A-Za-z0-9 \-]{3,10}$", message="Enter a valid postal code.")])
    latitude = FloatField("Latitude", validators=[Optional(), NumberRange(-90, 90)])
    longitude = FloatField("Longitude", validators=[Optional(), NumberRange(-180, 180)])
    hours = TextAreaField("Business hours", validators=[Optional(), Length(max=500)],
                          description="One line per day, e.g. Mon-Sat: 9:00 AM - 9:00 PM")
    description = TextAreaField("Description", validators=[Optional(), Length(max=600)])

    def validate(self, extra_validators=None):
        ok = super().validate(extra_validators)
        if ok and (self.latitude.data is None) != (self.longitude.data is None):
            self.longitude.errors = list(self.longitude.errors) + ["Enter both latitude and longitude, or leave both empty."]
            return False
        return ok


class PasswordForm(FlaskForm):
    current = PasswordField("Current password", validators=[DataRequired()])
    new = PasswordField("New password", validators=[DataRequired(), Length(min=8, max=72)])
    confirm = PasswordField("Confirm new password", validators=[DataRequired(), EqualTo("new", message="Passwords do not match.")])
