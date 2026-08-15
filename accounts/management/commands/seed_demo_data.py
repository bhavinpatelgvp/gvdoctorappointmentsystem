"""
Seed realistic DEMO DATA for Gujarat Vidyapith Doctor Appointment System.
All records are clearly marked as demo where applicable.
"""
import random
from datetime import date, time, timedelta, datetime
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction

from accounts.models import Role
from masters.models import Department, Programme, Specialization, HOD, MedicalSystem
from doctors.models import Doctor, DoctorSchedule
from patients.models import Patient, StudentProfile, StaffProfile, StaffFamilyProfile
from appointments.models import Appointment
from consultations.models import Consultation
from health_records.models import (
    ClinicalParameter, HealthCheckup, ClinicalParameterValue,
    CBCReport, RBSReport, BloodPressureReport, LipidProfileReport,
)
from certificates.models import MedicalCertificate

User = get_user_model()


class Command(BaseCommand):
    help = 'Load DEMO seed data for Gujarat Vidyapith Doctor System'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Seeding DEMO data...'))
        with transaction.atomic():
            self._roles()
            self._departments()
            self._programmes()
            self._specializations()
            self._medical_systems()
            self._clinical_parameters()
            self._users_and_profiles()
            self._appointments_and_health()
        self.stdout.write(self.style.SUCCESS('DEMO data seeded successfully.'))
        self.stdout.write('Login: admin / admin123  |  doctor1 / doctor123  |  student1 / student123')

    def _roles(self):
        roles = [
            (Role.ADMIN, 'Administrator'),
            (Role.DOCTOR, 'Doctor'),
            (Role.STUDENT, 'Student'),
            (Role.STAFF, 'Staff'),
            (Role.STAFF_FAMILY, 'Staff Family Member'),
            (Role.HOD, 'HOD'),
            (Role.SUPER_ADMIN, 'Super Administrator'),
        ]
        for code, name in roles:
            Role.objects.get_or_create(code=code, defaults={'name': name})
        self.stdout.write('  Roles created')

    def _departments(self):
        depts = [
            ('CS', 'Computer Science'),
            ('EDU', 'Education'),
            ('SS', 'Social Sciences'),
            ('GUJ', 'Gujarati'),
            ('MGT', 'Management'),
            ('SCI', 'Science'),
            ('HIN', 'Hindi'),
            ('ENG', 'English'),
        ]
        for code, name in depts:
            Department.objects.get_or_create(
                department_code=code, defaults={'name': name, 'status': 'Active'}
            )
        self.stdout.write('  Departments created')

    def _programmes(self):
        mapping = {
            'CS': [('BCA', 'Bachelor of Computer Applications', 3), ('MCA', 'Master of Computer Applications', 2)],
            'EDU': [('BEd', 'Bachelor of Education', 2), ('MEd', 'Master of Education', 2)],
            'SS': [('BA-SS', 'BA Social Sciences', 3)],
            'GUJ': [('BA-GUJ', 'BA Gujarati', 3)],
            'MGT': [('BBA', 'Bachelor of Business Administration', 3)],
            'SCI': [('BSc', 'Bachelor of Science', 3)],
        }
        for dcode, progs in mapping.items():
            dept = Department.objects.get(department_code=dcode)
            for pcode, pname, dur in progs:
                Programme.objects.get_or_create(
                    programme_code=pcode,
                    defaults={'name': pname, 'department': dept, 'duration_years': dur},
                )
        self.stdout.write('  Programmes created')

    def _specializations(self):
        specs = [
            ('GM', 'General Medicine'),
            ('PHY', 'Physician'),
            ('DER', 'Dermatology'),
            ('ORT', 'Orthopedics'),
            ('GYN', 'Gynecology'),
            ('ENT', 'ENT'),
            ('OPH', 'Ophthalmology'),
            ('CAR', 'Cardiology'),
        ]
        for code, name in specs:
            Specialization.objects.get_or_create(code=code, defaults={'name': name})
        self.stdout.write('  Specializations created')


    def _medical_systems(self):
        systems = [
            ('MBBS', 'MBBS / Allopathic'),
            ('AYUR', 'Ayurvedic'),
            ('HOME', 'Homeopathy'),
        ]
        for code, name in systems:
            MedicalSystem.objects.get_or_create(code=code, defaults={'name': name, 'status': 'Active'})
        self.stdout.write('  Medical systems created')

    def _clinical_parameters(self):
        params = [
            # CBC
            ('HB', 'Hemoglobin', 'cbc', 'g/dL', 12, 17, True, 13, 17, 12, 15),
            ('RBC', 'RBC Count', 'cbc', 'million/µL', 4.0, 5.5, False, None, None, None, None),
            ('WBC', 'WBC Count', 'cbc', '/µL', 4000, 11000, False, None, None, None, None),
            ('PLT', 'Platelet Count', 'cbc', '/µL', 150000, 450000, False, None, None, None, None),
            ('HCT', 'Hematocrit', 'cbc', '%', 36, 50, False, None, None, None, None),
            ('MCV', 'MCV', 'cbc', 'fL', 80, 100, False, None, None, None, None),
            ('MCH', 'MCH', 'cbc', 'pg', 27, 33, False, None, None, None, None),
            ('MCHC', 'MCHC', 'cbc', 'g/dL', 32, 36, False, None, None, None, None),
            ('NEU', 'Neutrophils', 'cbc', '%', 40, 70, False, None, None, None, None),
            ('LYM', 'Lymphocytes', 'cbc', '%', 20, 40, False, None, None, None, None),
            # RBS
            ('RBS', 'Random Blood Sugar', 'rbs', 'mg/dL', 70, 140, False, None, None, None, None),
            # BP
            ('SYS', 'Systolic BP', 'bp', 'mmHg', 90, 120, False, None, None, None, None),
            ('DIA', 'Diastolic BP', 'bp', 'mmHg', 60, 80, False, None, None, None, None),
            ('PULSE', 'Pulse Rate', 'bp', 'bpm', 60, 100, False, None, None, None, None),
            # Lipid
            ('TC', 'Total Cholesterol', 'lipid', 'mg/dL', 0, 200, False, None, None, None, None),
            ('HDL', 'HDL Cholesterol', 'lipid', 'mg/dL', 40, 60, False, None, None, None, None),
            ('LDL', 'LDL Cholesterol', 'lipid', 'mg/dL', 0, 100, False, None, None, None, None),
            ('TG', 'Triglycerides', 'lipid', 'mg/dL', 0, 150, False, None, None, None, None),
            # Other
            ('HT', 'Height', 'other', 'cm', None, None, False, None, None, None, None),
            ('WT', 'Weight', 'other', 'kg', None, None, False, None, None, None, None),
            ('BMI', 'BMI', 'other', 'kg/m²', 18.5, 24.9, False, None, None, None, None),
            ('TEMP', 'Temperature', 'other', '°C', 36.1, 37.2, False, None, None, None, None),
            ('SPO2', 'SpO2', 'other', '%', 95, 100, False, None, None, None, None),
        ]
        for i, p in enumerate(params):
            code, name, cat, unit, rmin, rmax, gspec, mmin, mmax, fmin, fmax = p
            ClinicalParameter.objects.get_or_create(
                code=code,
                defaults={
                    'name': name, 'category': cat, 'unit': unit,
                    'reference_min': rmin, 'reference_max': rmax,
                    'gender_specific': gspec,
                    'male_min': mmin, 'male_max': mmax,
                    'female_min': fmin, 'female_max': fmax,
                    'display_order': i,
                },
            )
        self.stdout.write('  Clinical parameters created')

    def _users_and_profiles(self):
        admin_role = Role.objects.get(code=Role.ADMIN)
        doctor_role = Role.objects.get(code=Role.DOCTOR)
        student_role = Role.objects.get(code=Role.STUDENT)
        staff_role = Role.objects.get(code=Role.STAFF)
        hod_role = Role.objects.get(code=Role.HOD)

        # Admin
        if not User.objects.filter(username='admin').exists():
            u = User.objects.create_superuser(
                username='admin', email='admin@gujaratvidyapith.ac.in',
                password='admin123', first_name='System', last_name='Administrator',
            )
            u.role = admin_role
            u.save()

        # Doctors
        doctor_data = [
            ('DOC001', 'doctor1', 'Rajesh', 'Patel', 'Male', 'GM', 'MD Medicine', 15),
            ('DOC002', 'doctor2', 'Meena', 'Shah', 'Female', 'PHY', 'MBBS, MD', 12),
            ('DOC003', 'doctor3', 'Amit', 'Desai', 'Male', 'ORT', 'MS Orthopedics', 10),
            ('DOC004', 'doctor4', 'Priya', 'Joshi', 'Female', 'DER', 'MD Dermatology', 8),
            ('DOC005', 'doctor5', 'Kiran', 'Trivedi', 'Male', 'ENT', 'MS ENT', 14),
            ('DOC006', 'doctor6', 'Sunita', 'Mehta', 'Female', 'GYN', 'MS Gynecology', 11),
            ('DOC007', 'doctor7', 'Nilesh', 'Parikh', 'Male', 'CAR', 'DM Cardiology', 18),
            ('DOC008', 'doctor8', 'Hetal', 'Raval', 'Female', 'OPH', 'MS Ophthalmology', 9),
        ]
        depts = list(Department.objects.all())
        for did, uname, fn, ln, gender, spec_code, qual, exp in doctor_data:
            if User.objects.filter(username=uname).exists():
                continue
            user = User.objects.create_user(
                username=uname, password='doctor123',
                email=f'{uname}@gujaratvidyapith.ac.in',
                first_name=fn, last_name=ln, role=doctor_role, gender=gender,
            )
            spec = Specialization.objects.get(code=spec_code)
            ms_list = list(MedicalSystem.objects.filter(status='Active'))
            doc = Doctor.objects.create(
                doctor_id=did, user=user, name=f'{fn} {ln}', gender=gender,
                qualification=qual, specialization=spec,
                medical_system=random.choice(ms_list) if ms_list else None,
                department=random.choice(depts),
                registration_number=f'GMC-{did}', email=user.email,
                mobile=f'98{random.randint(10000000,99999999)}',
                experience_years=exp, availability='Available', status='Active',
            )
            # Mon-Fri schedule
            for day in range(5):
                DoctorSchedule.objects.create(
                    doctor=doc, day_of_week=day,
                    start_time=time(9, 0), end_time=time(13, 0),
                    slot_duration_minutes=15, max_patients_per_day=20,
                    break_start=time(11, 0), break_end=time(11, 15),
                )
                DoctorSchedule.objects.create(
                    doctor=doc, day_of_week=day,
                    start_time=time(15, 0), end_time=time(17, 0),
                    slot_duration_minutes=15, max_patients_per_day=12,
                )

        # HODs
        for i, dept in enumerate(Department.objects.all()[:5]):
            uname = f'hod{i+1}'
            if User.objects.filter(username=uname).exists():
                continue
            user = User.objects.create_user(
                username=uname, password='hod123',
                email=f'{uname}@gujaratvidyapith.ac.in',
                first_name=f'HOD{i+1}', last_name=dept.name[:10], role=hod_role,
            )
            HOD.objects.create(
                employee_id=f'HOD{i+1:03d}', user=user, name=user.get_full_name(),
                department=dept, email=user.email, status='Active',
            )

        # Staff (25)
        designations = ['Clerk', 'Assistant', 'Librarian', 'Lab Assistant', 'Accountant', 'Office Superintendent']
        for i in range(1, 26):
            uname = f'staff{i}'
            if User.objects.filter(username=uname).exists():
                continue
            user = User.objects.create_user(
                username=uname, password='staff123',
                email=f'staff{i}@gujaratvidyapith.ac.in',
                first_name=f'Staff{i}', last_name='Member', role=staff_role,
                gender=random.choice(['Male', 'Female']),
            )
            emp_id = f'EMP{i:04d}'
            patient = Patient.objects.create(
                patient_id=f'P-STF-{i:04d}', user=user, category=Patient.CATEGORY_STAFF,
                name=user.get_full_name(), gender=user.gender,
                date_of_birth=date(1975 + i % 20, (i % 12) + 1, (i % 28) + 1),
                email=user.email, mobile=f'97{random.randint(10000000,99999999)}',
                blood_group=random.choice(['A+', 'B+', 'O+', 'AB+', 'A-', 'B-', 'O-']),
                status='Active',
            )
            StaffProfile.objects.create(
                patient=patient, employee_id=emp_id,
                department=random.choice(depts),
                designation=random.choice(designations),
            )
            # 1-2 family members for some staff
            if i <= 15:
                for j, rel in enumerate(random.sample(['Spouse', 'Son', 'Daughter', 'Father', 'Mother'], k=random.randint(1, 2))):
                    fp = Patient.objects.create(
                        patient_id=f'P-FAM-{i:04d}-{j}',
                        category=Patient.CATEGORY_STAFF_FAMILY,
                        name=f'{rel} of Staff{i}',
                        gender='Female' if rel in ('Spouse', 'Daughter', 'Mother') else 'Male',
                        date_of_birth=date(1980 + j * 5, 5, 15),
                        mobile=f'96{random.randint(10000000,99999999)}',
                        blood_group=random.choice(['A+', 'B+', 'O+']),
                        status='Active',
                    )
                    StaffFamilyProfile.objects.create(
                        patient=fp,
                        related_staff=patient.staff_profile,
                        relationship=rel,
                    )

        # Students (80)
        programmes = list(Programme.objects.all())
        for i in range(1, 81):
            uname = f'student{i}'
            if User.objects.filter(username=uname).exists():
                continue
            user = User.objects.create_user(
                username=uname, password='student123',
                email=f'student{i}@gujaratvidyapith.ac.in',
                first_name=f'Student{i}', last_name=random.choice(['Patel', 'Shah', 'Mehta', 'Joshi', 'Desai', 'Raval']),
                role=student_role, gender=random.choice(['Male', 'Female']),
            )
            prog = random.choice(programmes)
            patient = Patient.objects.create(
                patient_id=f'P-STU-{i:04d}', user=user, category=Patient.CATEGORY_STUDENT,
                name=user.get_full_name(), gender=user.gender,
                date_of_birth=date(2000 + (i % 6), (i % 12) + 1, (i % 28) + 1),
                email=user.email, mobile=f'95{random.randint(10000000,99999999)}',
                blood_group=random.choice(['A+', 'B+', 'O+', 'AB+', 'A-', 'B-', 'O-']),
                status='Active',
            )
            StudentProfile.objects.create(
                patient=patient,
                enrollment_number=f'GV{2020 + (i % 5)}{i:04d}',
                programme=prog, department=prog.department,
                semester=random.randint(1, 6),
            )
        self.stdout.write('  Users, doctors, staff, students, family created')

    def _appointments_and_health(self):
        """Seed appointments with unique doctor/date/time slots to satisfy UNIQUE constraint."""
        from django.db import IntegrityError

        doctors = list(Doctor.objects.all())
        patients = list(Patient.objects.filter(status='Active'))
        if not doctors or not patients:
            self.stdout.write(self.style.WARNING('  No doctors/patients – skipping appointments'))
            return

        today = date.today()
        statuses = [
            Appointment.STATUS_COMPLETED,
            Appointment.STATUS_CONFIRMED,
            Appointment.STATUS_REQUESTED,
            Appointment.STATUS_CANCELLED,
        ]
        slot_minutes = [0, 15, 30, 45]
        used_slots = set()  # (doctor_id, date, time)
        # Pre-load existing slots if re-running seed
        for row in Appointment.objects.values_list('doctor_id', 'appointment_date', 'appointment_time'):
            used_slots.add(row)

        appt_count = 0
        attempts = 0
        target = 120
        i = 0
        while appt_count < target and attempts < target * 5:
            attempts += 1
            i += 1
            pat = random.choice(patients)
            doc = random.choice(doctors)
            days_ago = random.randint(-10, 60)
            adate = today - timedelta(days=days_ago)
            # Prefer unique slot; try a few times
            atime = None
            for _ in range(20):
                candidate = time(random.randint(9, 16), random.choice(slot_minutes))
                key = (doc.pk, adate, candidate)
                if key not in used_slots:
                    atime = candidate
                    break
            if atime is None:
                continue

            status = random.choice(statuses) if days_ago > 0 else random.choice(
                [Appointment.STATUS_CONFIRMED, Appointment.STATUS_REQUESTED]
            )
            num = f'APT{adate.strftime("%Y%m%d")}{i:04d}'
            if Appointment.objects.filter(appointment_number=num).exists():
                num = f'APT{adate.strftime("%Y%m%d")}{i:04d}{random.randint(10, 99)}'

            try:
                # Savepoint so IntegrityError does not break the outer atomic block
                with transaction.atomic():
                    appt = Appointment.objects.create(
                        appointment_number=num, patient=pat, doctor=doc,
                        appointment_date=adate, appointment_time=atime,
                        status=status, reason='General consultation (DEMO)',
                    )
                    used_slots.add((doc.pk, adate, atime))
                    appt_count += 1

                    if status != Appointment.STATUS_COMPLETED:
                        continue

                    cons = Consultation.objects.create(
                        appointment=appt, patient=pat, doctor=doc,
                        consultation_date=timezone.make_aware(datetime.combine(adate, atime)),
                        chief_complaint='Fever / General weakness (DEMO)',
                        symptoms='Mild symptoms',
                        preliminary_diagnosis='Viral fever (DEMO)',
                        final_diagnosis='Viral fever – resolved (DEMO)',
                        treatment='Rest and hydration',
                        prescription='Paracetamol 500mg SOS',
                        advice='Plenty of fluids',
                        rest_recommended=random.choice([True, False]),
                        rest_days=random.choice([None, 2, 3, 5]),
                    )
                    hc = HealthCheckup.objects.create(
                        patient=pat, doctor=doc, checkup_date=adate,
                        notes='DEMO health checkup', is_demo=True,
                    )
                    hb = Decimal(str(round(random.uniform(10.5, 16.5), 1)))
                    CBCReport.objects.create(
                        health_checkup=hc,
                        hemoglobin=hb,
                        rbc_count=Decimal(str(round(random.uniform(4.0, 5.5), 2))),
                        wbc_count=Decimal(str(random.randint(4500, 10500))),
                        platelet_count=Decimal(str(random.randint(160000, 400000))),
                        hematocrit=Decimal(str(round(random.uniform(36, 48), 1))),
                        neutrophils=Decimal(str(round(random.uniform(45, 65), 1))),
                        lymphocytes=Decimal(str(round(random.uniform(25, 40), 1))),
                    )
                    rbs_val = Decimal(str(round(random.uniform(80, 180), 1)))
                    RBSReport.objects.create(health_checkup=hc, value=rbs_val)
                    BloodPressureReport.objects.create(
                        health_checkup=hc,
                        systolic=random.randint(105, 145),
                        diastolic=random.randint(65, 95),
                        pulse_rate=random.randint(65, 95),
                        measured_at=timezone.make_aware(datetime.combine(adate, atime)),
                    )
                    if random.random() > 0.4:
                        LipidProfileReport.objects.create(
                            health_checkup=hc,
                            total_cholesterol=Decimal(str(random.randint(150, 250))),
                            hdl=Decimal(str(random.randint(35, 65))),
                            ldl=Decimal(str(random.randint(80, 160))),
                            triglycerides=Decimal(str(random.randint(80, 220))),
                        )
                    for code, val in [('HB', hb), ('RBS', rbs_val)]:
                        param = ClinicalParameter.objects.filter(code=code).first()
                        if param:
                            cpv = ClinicalParameterValue(
                                health_checkup=hc, parameter=param, value=val, unit=param.unit
                            )
                            cpv.evaluate_status(pat.gender)
                            cpv.save()
                    if cons.rest_recommended and random.random() > 0.5:
                        MedicalCertificate.objects.create(
                            certificate_number=f'CERT-{num}',
                            patient=pat, doctor=doc, consultation=cons,
                            consultation_date=adate,
                            medical_advice='Rest advised (DEMO)',
                            rest_recommended=True,
                            rest_start_date=adate,
                            rest_end_date=adate + timedelta(days=cons.rest_days or 2),
                            rest_days=cons.rest_days or 2,
                            status=MedicalCertificate.STATUS_ISSUED,
                            issued_at=timezone.now(),
                        )
            except IntegrityError:
                # Slot taken (race or constraint) – skip and try another
                continue
            except Exception as exc:
                self.stdout.write(self.style.WARNING(f'  Skip appointment seed item: {exc}'))
                continue

        self.stdout.write(f'  Appointments & health records created (~{appt_count})')
