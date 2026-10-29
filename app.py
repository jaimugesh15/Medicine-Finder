"""MedicineFinder - Flask application factory and development commands."""
import random
from datetime import timedelta

import click
from flask import Flask, render_template

from config import Config
from extensions import csrf, db, login_manager
from models import Medicine, Pharmacy, User, now


def create_app(config=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config)
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from routes.auth import bp as auth_bp
    from routes.dashboard import bp as dashboard_bp
    from routes.public import bp as public_bp
    for bp in (public_bp, auth_bp, dashboard_bp):
        app.register_blueprint(bp)

    @app.template_filter("dt")
    def fmt_dt(value):
        return value.strftime("%d %b %Y, %I:%M %p") if value else "-"

    @app.template_filter("ago")
    def ago(value):
        if not value:
            return "Never"
        s = (now() - value).total_seconds()
        if s < 60:
            return "Just now"
        if s < 3600:
            return f"{int(s // 60)} min ago"
        if s < 86400:
            return f"{int(s // 3600)} h ago"
        if s < 86400 * 7:
            return f"{int(s // 86400)} d ago"
        return value.strftime("%d %b %Y")

    @app.errorhandler(404)
    def not_found(e):
        return render_template("error.html", code=404, message="That page could not be found."), 404

    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback()
        return render_template("error.html", code=500, message="Something went wrong on our side."), 500

    with app.app_context():
        db.create_all()          # creates missing tables only; never deletes data
    register_commands(app)
    return app


# ---------------------------------------------------------------- development commands
SAMPLES = [  # (name, address, lat, lng) - fictional pharmacies, approximate sample locations
    ("Sample Community Pharmacy", "Sample Street 1, White Town", 11.9340, 79.8300),
    ("Sample City Care Pharmacy", "Sample Road 2, Muthialpet", 11.9450, 79.8080),
    ("Sample Green Cross Pharmacy", "Sample Avenue 3, Lawspet", 11.9600, 79.8120),
    ("Sample Lakeside Pharmacy", "Sample Lane 4, Reddiarpalayam", 11.9560, 79.8240),
]
MEDS = [("Paracetamol", "500 mg", "Tablet", "Pain & fever"), ("Ibuprofen", "400 mg", "Tablet", "Pain & fever"),
        ("Cetirizine", "10 mg", "Tablet", "Cold & allergy"), ("Amoxicillin", "500 mg", "Capsule", "Antibiotics"),
        ("Azithromycin", "500 mg", "Tablet", "Antibiotics"), ("Metformin", "500 mg", "Tablet", "Diabetes care"),
        ("Amlodipine", "5 mg", "Tablet", "Heart & blood pressure"), ("Omeprazole", "20 mg", "Capsule", "Digestive health"),
        ("ORS", "", "Sachet / powder", "Digestive health"), ("Vitamin C", "500 mg", "Tablet", "Vitamins & supplements"),
        ("Antiseptic solution", "", "", "First aid & supplies"), ("Adhesive bandage", "", "", "First aid & supplies")]


def register_commands(app):
    @app.cli.command("seed-demo")
    @click.option("--password", required=True, help="Password for demo@medicinefinder.local")
    def seed_demo(password):
        """DEVELOPMENT ONLY: add clearly labelled SAMPLE pharmacies and a demo login."""
        if User.query.filter_by(email="demo@medicinefinder.local").first():
            click.echo("Demo data already exists. Use `flask reset-db --yes` to start again.")
            return
        rng = random.Random(7)
        user = User(email="demo@medicinefinder.local", full_name="Demo Manager")
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        for i, (name, addr, lat, lng) in enumerate(SAMPLES):
            ph = Pharmacy(name=name, address=addr, city="Puducherry", latitude=lat, longitude=lng,
                          phone=f"+91 00000 0000{i}", manager_name="Sample Manager", is_demo=True,
                          hours="Mon-Sat: 9:00 AM - 9:00 PM\nSun: 10:00 AM - 2:00 PM",
                          description="SAMPLE pharmacy created for demonstration. Not a real business.",
                          owner_id=user.id if i == 0 else None)
            db.session.add(ph)
            db.session.flush()
            for n, s, f, cat in MEDS:
                if rng.random() < 0.2:
                    continue
                db.session.add(Medicine(pharmacy_id=ph.id, name=n, strength=s, dosage_form=f, category=cat,
                                        quantity=rng.choice([0, 3, 8, 25, 60, 120]), reorder_level=10,
                                        verified=True, last_verified_at=now() - timedelta(hours=rng.randint(1, 48)),
                                        notes="Sample record"))
        db.session.commit()
        click.echo("Sample data created. Login: demo@medicinefinder.local with the password you gave.")

    @app.cli.command("reset-db")
    @click.option("--yes", is_flag=True, help="Confirm that ALL data will be deleted")
    def reset_db(yes):
        """DEVELOPMENT ONLY: delete every table and recreate it empty."""
        if not yes:
            click.echo("This deletes all data. Run again with --yes to confirm.")
            return
        db.drop_all()
        db.create_all()
        click.echo("Database reset.")


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
