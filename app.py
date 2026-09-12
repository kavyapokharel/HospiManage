from __future__ import annotations

import os
from datetime import date, datetime
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import CheckConstraint, UniqueConstraint, or_
from werkzeug.security import check_password_hash, generate_password_hash
from wtforms import DateField, DateTimeLocalField, EmailField, PasswordField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional, ValidationError

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'hospimanage.db')}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

db = SQLAlchemy(app)

csrf = CSRFProtect(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "warning"


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="staff")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_code = db.Column(db.String(20), nullable=False, unique=True, index=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    sex = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    emergency_contact = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    appointments = db.relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")
    records = db.relationship("MedicalRecord", back_populates="patient", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("length(patient_code) >= 3", name="ck_patient_code_length"),
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id", ondelete="CASCADE"), nullable=False, index=True)
    scheduled_for = db.Column(db.DateTime, nullable=False, index=True)
    department = db.Column(db.String(80), nullable=False)
    clinician = db.Column(db.String(120), nullable=False)
    reason = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Scheduled")
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    patient = db.relationship("Patient", back_populates="appointments")

    __table_args__ = (
        CheckConstraint(
            "status in ('Scheduled','Completed','Cancelled','No-show')",
            name="ck_appointment_status",
        ),
        UniqueConstraint("clinician", "scheduled_for", name="uq_clinician_timeslot"),
    )


class MedicalRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id", ondelete="CASCADE"), nullable=False, index=True)
    encounter_date = db.Column(db.Date, nullable=False, default=date.today)
    diagnosis = db.Column(db.String(255), nullable=False)
    treatment = db.Column(db.Text, nullable=True)
    medications = db.Column(db.Text, nullable=True)
    clinical_notes = db.Column(db.Text, nullable=True)
    author = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    patient = db.relationship("Patient", back_populates="records")


@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(User, int(user_id))


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6, max=128)])
    submit = SubmitField("Sign in")


class PatientForm(FlaskForm):
    patient_code = StringField("Patient ID", validators=[DataRequired(), Length(min=3, max=20)])
    first_name = StringField("First name", validators=[DataRequired(), Length(max=80)])
    last_name = StringField("Last name", validators=[DataRequired(), Length(max=80)])
    date_of_birth = DateField("Date of birth", validators=[DataRequired()])
    sex = SelectField("Sex", choices=[("Female", "Female"), ("Male", "Male"), ("Other", "Other")], validators=[DataRequired()])
    phone = StringField("Phone", validators=[Optional(), Length(max=30)])
    email = EmailField("Email", validators=[Optional(), Email(), Length(max=120)])
    address = StringField("Address", validators=[Optional(), Length(max=255)])
    emergency_contact = StringField("Emergency contact", validators=[Optional(), Length(max=120)])
    submit = SubmitField("Save patient")

    def validate_date_of_birth(self, field):
        if field.data and field.data > date.today():
            raise ValidationError("Date of birth cannot be in the future.")


class AppointmentForm(FlaskForm):
    patient_id = SelectField("Patient", coerce=int, validators=[DataRequired()])
    scheduled_for = DateTimeLocalField("Date & time", format="%Y-%m-%dT%H:%M", validators=[DataRequired()])
    department = StringField("Department", validators=[DataRequired(), Length(max=80)])
    clinician = StringField("Clinician", validators=[DataRequired(), Length(max=120)])
    reason = StringField("Reason", validators=[DataRequired(), Length(max=255)])
    status = SelectField(
        "Status",
        choices=[("Scheduled", "Scheduled"), ("Completed", "Completed"), ("Cancelled", "Cancelled"), ("No-show", "No-show")],
        validators=[DataRequired()],
    )
    notes = TextAreaField("Notes", validators=[Optional(), Length(max=3000)])
    submit = SubmitField("Save appointment")


class RecordForm(FlaskForm):
    patient_id = SelectField("Patient", coerce=int, validators=[DataRequired()])
    encounter_date = DateField("Encounter date", validators=[DataRequired()], default=date.today)
    diagnosis = StringField("Diagnosis", validators=[DataRequired(), Length(max=255)])
    treatment = TextAreaField("Treatment", validators=[Optional(), Length(max=3000)])
    medications = TextAreaField("Medications", validators=[Optional(), Length(max=2000)])
    clinical_notes = TextAreaField("Clinical notes", validators=[Optional(), Length(max=5000)])
    author = StringField("Author / clinician", validators=[DataRequired(), Length(max=120)])
    submit = SubmitField("Save medical record")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data.strip()).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.", "danger")
    return render_template("login.html", form=form)


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Signed out.", "success")
    return redirect(url_for("login"))


@app.route("/")
@login_required
def dashboard():
    today = date.today()
    patient_count = Patient.query.count()
    appointment_count = Appointment.query.count()
    record_count = MedicalRecord.query.count()
    upcoming = (
        Appointment.query.filter(Appointment.scheduled_for >= datetime.now())
        .order_by(Appointment.scheduled_for.asc())
        .limit(6)
        .all()
    )
    return render_template(
        "dashboard.html",
        patient_count=patient_count,
        appointment_count=appointment_count,
        record_count=record_count,
        upcoming=upcoming,
        today=today,
    )


@app.route("/patients")
@login_required
def patients():
    q = request.args.get("q", "").strip()
    query = Patient.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Patient.patient_code.ilike(like),
                Patient.first_name.ilike(like),
                Patient.last_name.ilike(like),
                Patient.phone.ilike(like),
            )
        )
    rows = query.order_by(Patient.last_name.asc(), Patient.first_name.asc()).all()
    return render_template("patients.html", patients=rows, q=q)


@app.route("/patients/new", methods=["GET", "POST"])
@login_required
def patient_new():
    form = PatientForm()
    if form.validate_on_submit():
        code = form.patient_code.data.strip().upper()
        if Patient.query.filter_by(patient_code=code).first():
            form.patient_code.errors.append("That patient ID already exists.")
        else:
            patient = Patient(
                patient_code=code,
                first_name=form.first_name.data.strip(),
                last_name=form.last_name.data.strip(),
                date_of_birth=form.date_of_birth.data,
                sex=form.sex.data,
                phone=(form.phone.data or "").strip() or None,
                email=(form.email.data or "").strip().lower() or None,
                address=(form.address.data or "").strip() or None,
                emergency_contact=(form.emergency_contact.data or "").strip() or None,
            )
            db.session.add(patient)
            db.session.commit()
            flash("Patient created.", "success")
            return redirect(url_for("patient_detail", patient_id=patient.id))
    return render_template("patient_form.html", form=form, title="New patient")


@app.route("/patients/<int:patient_id>")
@login_required
def patient_detail(patient_id: int):
    patient = db.get_or_404(Patient, patient_id)
    appointments = Appointment.query.filter_by(patient_id=patient.id).order_by(Appointment.scheduled_for.desc()).all()
    records = MedicalRecord.query.filter_by(patient_id=patient.id).order_by(MedicalRecord.encounter_date.desc()).all()
    return render_template("patient_detail.html", patient=patient, appointments=appointments, records=records)


@app.route("/patients/<int:patient_id>/edit", methods=["GET", "POST"])
@login_required
def patient_edit(patient_id: int):
    patient = db.get_or_404(Patient, patient_id)
    form = PatientForm(obj=patient)
    if form.validate_on_submit():
        code = form.patient_code.data.strip().upper()
        duplicate = Patient.query.filter(Patient.patient_code == code, Patient.id != patient.id).first()
        if duplicate:
            form.patient_code.errors.append("That patient ID already exists.")
        else:
            patient.patient_code = code
            patient.first_name = form.first_name.data.strip()
            patient.last_name = form.last_name.data.strip()
            patient.date_of_birth = form.date_of_birth.data
            patient.sex = form.sex.data
            patient.phone = (form.phone.data or "").strip() or None
            patient.email = (form.email.data or "").strip().lower() or None
            patient.address = (form.address.data or "").strip() or None
            patient.emergency_contact = (form.emergency_contact.data or "").strip() or None
            db.session.commit()
            flash("Patient updated.", "success")
            return redirect(url_for("patient_detail", patient_id=patient.id))
    return render_template("patient_form.html", form=form, title="Edit patient")


@app.route("/appointments")
@login_required
def appointments():
    rows = Appointment.query.order_by(Appointment.scheduled_for.desc()).all()
    return render_template("appointments.html", appointments=rows)


def populate_patient_choices(form):
    form.patient_id.choices = [
        (p.id, f"{p.patient_code} — {p.full_name}")
        for p in Patient.query.order_by(Patient.last_name, Patient.first_name).all()
    ]


@app.route("/appointments/new", methods=["GET", "POST"])
@login_required
def appointment_new():
    form = AppointmentForm()
    populate_patient_choices(form)
    patient_id = request.args.get("patient_id", type=int)
    if request.method == "GET" and patient_id:
        form.patient_id.data = patient_id
    if form.validate_on_submit():
        conflict = Appointment.query.filter_by(
            clinician=form.clinician.data.strip(), scheduled_for=form.scheduled_for.data
        ).first()
        if conflict:
            form.scheduled_for.errors.append("That clinician already has an appointment at this time.")
        else:
            appt = Appointment(
                patient_id=form.patient_id.data,
                scheduled_for=form.scheduled_for.data,
                department=form.department.data.strip(),
                clinician=form.clinician.data.strip(),
                reason=form.reason.data.strip(),
                status=form.status.data,
                notes=(form.notes.data or "").strip() or None,
            )
            db.session.add(appt)
            db.session.commit()
            flash("Appointment scheduled.", "success")
            return redirect(url_for("appointments"))
    return render_template("appointment_form.html", form=form)


@app.route("/appointments/<int:appointment_id>/status", methods=["POST"])
@login_required
def appointment_status(appointment_id: int):
    appt = db.get_or_404(Appointment, appointment_id)
    status = request.form.get("status", "")
    allowed = {"Scheduled", "Completed", "Cancelled", "No-show"}
    if status not in allowed:
        flash("Invalid status.", "danger")
    else:
        appt.status = status
        db.session.commit()
        flash("Appointment status updated.", "success")
    return redirect(request.referrer or url_for("appointments"))


@app.route("/records")
@login_required
def records():
    rows = MedicalRecord.query.order_by(MedicalRecord.encounter_date.desc()).all()
    return render_template("records.html", records=rows)


@app.route("/records/new", methods=["GET", "POST"])
@login_required
def record_new():
    form = RecordForm()
    populate_patient_choices(form)
    patient_id = request.args.get("patient_id", type=int)
    if request.method == "GET" and patient_id:
        form.patient_id.data = patient_id
    if form.validate_on_submit():
        record = MedicalRecord(
            patient_id=form.patient_id.data,
            encounter_date=form.encounter_date.data,
            diagnosis=form.diagnosis.data.strip(),
            treatment=(form.treatment.data or "").strip() or None,
            medications=(form.medications.data or "").strip() or None,
            clinical_notes=(form.clinical_notes.data or "").strip() or None,
            author=form.author.data.strip(),
        )
        db.session.add(record)
        db.session.commit()
        flash("Medical record added.", "success")
        return redirect(url_for("patient_detail", patient_id=record.patient_id))
    return render_template("record_form.html", form=form)


def seed_demo_data():
    if not User.query.filter_by(username="admin").first():
        admin = User(username="admin", role="admin")
        admin.set_password(os.environ.get("ADMIN_PASSWORD", "admin123"))
        db.session.add(admin)
        db.session.commit()


with app.app_context():
    db.create_all()
    seed_demo_data()


if __name__ == "__main__":
    app.run(debug=True)
