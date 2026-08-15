# Gujarat Vidyapith Doctor Appointment, Patient Management & Health Check-up Analytics System

Professional Django-based healthcare platform for Gujarat Vidyapith.

## Features (Current Prototype)

- **Role-based access**: Administrator, Doctor, Student, Staff, Staff Family, HOD
- **Master data**: Departments, Programmes, Specializations, HODs, Doctors, Schedules
- **Patient management**: Unified Patient model with Student / Staff / Staff-Family profiles
- **Appointments**: Booking statuses, double-booking constraint, doctor schedules
- **Consultations**: Full clinical documentation linked to appointments
- **Health records**: CBC, RBS, BP, Lipid Profile + extensible ClinicalParameter framework
- **Medical certificates**: Issuance workflow with rest recommendation
- **Audit logging**: Login/logout and critical actions
- **Demo data**: ~80 students, 25 staff, family members, 8 doctors, 120 appointments, health reports
- **UI**: Gujarat Vidyapith-inspired cream / earthy-brown academic theme (Bootstrap 5)

## Technology Stack

- Python 3.11+ / Django 5.x–6.x
- SQLite (demo) → MySQL/PostgreSQL ready via environment variables
- Django ORM, Authentication, Crispy Forms, REST Framework (API-ready)
- Bootstrap 5, Chart.js-ready structure

## Google (Gmail) sign-in

1. Install: `pip install -r requirements.txt` (includes `django-allauth`)
2. Create OAuth client in [Google Cloud Console](https://console.cloud.google.com/) (Web application).
3. Authorized redirect URI: `http://127.0.0.1:8000/accounts/google/login/callback/`
4. Put `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env`
5. Run migrations: `python manage.py migrate`
6. Ensure Site domain is `127.0.0.1:8000` in Django admin → Sites (or `python manage.py shell` update).

Login page shows **Sign in with Gmail**. Existing users are matched by email; new Gmail users complete Patient or Doctor registration.

## Quick Start

```bash
cd /path/to/project
python -m venv .venv && source .venv/bin/activate   # optional
pip install -r requirements.txt
cp .env.example .env

# Database (demo uses SQLite path from settings / env)
python manage.py migrate
python manage.py seed_demo_data

python manage.py runserver
```

Open http://127.0.0.1:8000/

### Demo Logins

| Username  | Password    | Role          |
|-----------|-------------|---------------|
| admin     | admin123    | Administrator |
| doctor1   | doctor123   | Doctor        |
| student1  | student123  | Student       |
| staff1    | staff123    | Staff         |
| hod1      | hod123      | HOD           |

## Project Structure

```
config/          – settings, root URLs
accounts/        – User, Role, auth, dashboards
masters/         – Department, Programme, Specialization, HOD
patients/        – Patient + category profiles
doctors/         – Doctor, Schedule, Leave
appointments/    – Appointment booking
consultations/   – Consultation notes
health_records/  – CBC/RBS/BP/Lipid + ClinicalParameter + bulk import log
certificates/    – Medical certificates
notifications/   – In-app notifications
analytics/       – Analytics views (extensible)
audit/           – AuditLog + middleware + services
templates/       – Django templates
static/          – CSS (gv-theme.css), JS, images
fixtures/        – Optional fixtures
imports/         – Bulk import workspace
```

## Production Database

Set in `.env`:

```
DB_ENGINE=django.db.backends.mysql   # or postgresql
DB_NAME=gv_doctor
DB_USER=...
DB_PASSWORD=...
DB_HOST=127.0.0.1
DB_PORT=3306
```

Then `python manage.py migrate`.

## Security Notes

- Never commit `.env` or real credentials
- Medical data access is role-scoped (minimum necessary)
- Audit trail records sensitive actions
- Soft status fields used for master data deactivation

## Extending

- Add REST endpoints via DRF serializers in each app
- Expand analytics with Chart.js / Plotly using `health_records` aggregates
- Implement bulk CSV/Excel import using `BulkImportLog` and pandas
- Wire SMTP for appointment/certificate notifications

## License / Branding

Prototype for Gujarat Vidyapith institutional use. Use official logo assets only when supplied by the institution. Do not invent official seals.
