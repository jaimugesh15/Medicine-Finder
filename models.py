"""Database models: User, Pharmacy, Medicine (inventory item), InventoryActivity."""
from datetime import datetime

from flask_login import UserMixin
from sqlalchemy import and_
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db

STATUS_LABELS = {"available": "Available", "low": "Low stock",
                 "out": "Out of stock", "unknown": "Unknown"}


def now():
    return datetime.now().replace(microsecond=0)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=now)
    pharmacy = db.relationship("Pharmacy", back_populates="owner", uselist=False)

    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password_hash, raw)

    @property
    def initials(self):
        parts = self.full_name.split()
        return "".join(p[0] for p in parts[:2]).upper() or "U"


class Pharmacy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True)
    name = db.Column(db.String(120), nullable=False)
    manager_name = db.Column(db.String(100))
    phone = db.Column(db.String(25))
    email = db.Column(db.String(120))
    address = db.Column(db.String(200))
    city = db.Column(db.String(80), index=True)
    postal_code = db.Column(db.String(12))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    hours = db.Column(db.Text)          # one line per day, e.g. "Mon-Sat: 9:00-21:00"
    description = db.Column(db.Text)
    is_demo = db.Column(db.Boolean, default=False, nullable=False)  # sample data flag
    created_at = db.Column(db.DateTime, default=now)
    updated_at = db.Column(db.DateTime, default=now, onupdate=now)
    owner = db.relationship("User", back_populates="pharmacy")
    medicines = db.relationship("Medicine", back_populates="pharmacy",
                                cascade="all, delete-orphan")

    @property
    def has_coordinates(self):
        return self.latitude is not None and self.longitude is not None

    @property
    def completion(self):
        """Percentage of useful public profile fields that are filled in."""
        fields = [self.name, self.manager_name, self.phone, self.email, self.address,
                  self.city, self.postal_code, self.hours, self.description,
                  self.latitude if self.has_coordinates else None]
        return int(100 * sum(1 for f in fields if f not in (None, "")) / len(fields))


class Medicine(db.Model):
    __table_args__ = (db.UniqueConstraint("pharmacy_id", "name", "strength", "dosage_form",
                                          name="uq_medicine_per_pharmacy"),)
    id = db.Column(db.Integer, primary_key=True)
    pharmacy_id = db.Column(db.Integer, db.ForeignKey("pharmacy.id"), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    category = db.Column(db.String(60), nullable=False)
    strength = db.Column(db.String(40), default="", nullable=False)
    dosage_form = db.Column(db.String(40), default="", nullable=False)
    manufacturer = db.Column(db.String(100))
    quantity = db.Column(db.Integer, default=0, nullable=False)
    reorder_level = db.Column(db.Integer, default=10, nullable=False)
    verified = db.Column(db.Boolean, default=False, nullable=False)
    notes = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=now)
    updated_at = db.Column(db.DateTime, default=now, onupdate=now)
    last_verified_at = db.Column(db.DateTime)
    pharmacy = db.relationship("Pharmacy", back_populates="medicines")

    @property
    def status(self):
        """Stock-status rules (single source of truth):
        not verified -> unknown | 0 -> out | <= reorder level -> low | else available"""
        if not self.verified or self.quantity is None:
            return "unknown"
        if self.quantity == 0:
            return "out"
        if self.quantity <= self.reorder_level:
            return "low"
        return "available"

    @staticmethod
    def status_filter(status):
        """The same rules as `status`, as an SQL condition (used by search/filter)."""
        if status == "unknown":
            return Medicine.verified.is_(False)
        v = Medicine.verified.is_(True)
        return {"out": and_(v, Medicine.quantity == 0),
                "low": and_(v, Medicine.quantity > 0, Medicine.quantity <= Medicine.reorder_level),
                "available": and_(v, Medicine.quantity > Medicine.reorder_level)}.get(status)

    @property
    def display_name(self):
        return " ".join(x for x in (self.name, self.strength, self.dosage_form) if x)


class InventoryActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pharmacy_id = db.Column(db.Integer, db.ForeignKey("pharmacy.id"), nullable=False, index=True)
    medicine_id = db.Column(db.Integer)          # kept even after the medicine is deleted
    medicine_name = db.Column(db.String(200), nullable=False)
    action = db.Column(db.String(30), nullable=False)   # Added / Updated / Deleted
    previous_status = db.Column(db.String(20))
    current_status = db.Column(db.String(20))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.DateTime, default=now, index=True)
    user = db.relationship("User")
