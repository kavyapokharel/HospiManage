# HospiManage — Full-Stack Hospital Management System

HospiManage is a full-stack web application for patient administration, appointment scheduling, and basic electronic health record (EHR) workflows.

This version modernizes the original console-based C++ patient-record project (`legacy/HospiManage.cpp`) into a web application.

## Tech stack
- **Backend:** Python, Flask
- **Database:** SQLite + SQLAlchemy ORM
- **Frontend:** HTML, CSS, Jinja templates
- **Security / validation:** Flask-Login, password hashing with Werkzeug, CSRF protection through Flask-WTF, server-side form validation, database uniqueness/check constraints

## Features
- Staff login/logout
- Patient creation, search, detail view, and editing
- Appointment scheduling with clinician/time conflict prevention
- Appointment status workflow
- EHR entries for diagnosis, treatment, medication, and clinical notes
- Relational database schema with foreign keys and cascading relationships
- Server-side validation and duplicate patient-ID prevention
- Responsive dashboard

## Run locally

```bash
python -m venv .venv
# Windows:
.venv\\Scripts\\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

Demo credentials:
- username: `admin`
- password: `admin123`

For anything beyond a local demo, set environment variables `SECRET_KEY` and `ADMIN_PASSWORD`, use a production database, HTTPS, access controls, audit logging, backups, and institution-specific compliance controls.

## Data model

**User**
- username, password hash, role

**Patient**
- unique patient code
- name, DOB, sex
- contact and emergency-contact information

**Appointment**
- patient relationship
- date/time, department, clinician, reason, status, notes
- unique clinician/time constraint

**MedicalRecord**
- patient relationship
- encounter date, diagnosis, treatment, medications, clinical notes, author

## Interview explanation

The original version was a C++ console application that stored patient records in binary files. The full-stack version preserves the patient-management idea but separates concerns into:

1. a Flask web backend,
2. a relational SQL database,
3. HTML/CSS user interfaces,
4. validated web forms,
5. authenticated staff access.

This is a portfolio/demo project and is not intended for production clinical use.
