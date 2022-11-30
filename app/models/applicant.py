import enum
from app.database import db
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey


class ProgramMapping(db.Model):
    program_type = db.Column(db.String(10), primary_key=True, autoincrement=False)


class Program(db.Model):
    code = db.Column(db.String(10), primary_key=True, unique=True, autoincrement=False)
    name = db.Column(db.String(120))
    academic_level = db.Column(db.String(120))
    active = db.Column(db.Boolean, default=True)
    program_type = db.Column(db.String(10), ForeignKey("program_mapping.program_type"))


class Applicant(db.Model):
    version = db.Column(
        db.Integer,
        ForeignKey("file_control.version"),
        primary_key=True,
    )
    program_code = db.Column(
        db.String(10), ForeignKey("program.code"), primary_key=True
    )
    anticipated_entry_term = db.Column(db.String(30))
    admissions_cycle = db.Column(db.Integer)
    erpid = db.Column(db.Integer, primary_key=True)
    prefix = db.Column(db.String(10))
    first_name = db.Column(db.String(80))
    last_name = db.Column(db.String(80))
    gender = db.Column(db.String)
    birth_date = db.Column(db.Date)
    nationality = db.Column(db.String(100))
    ethnicity = db.Column(db.String)
    disability = db.Column(db.String)
    country_of_residency = db.Column(db.String)
    email = db.Column(db.String(120))
    application_folder_fee_status = db.Column(db.String(20))
    combined_fee_status = db.Column(db.String(20))
    application_status = db.Column(db.String(80))
    supplemental_complete = db.Column(db.Boolean)
    academic_eligibility = db.Column(db.String(80))
    folder_status = db.Column(db.String(80))
    date_to_department = db.Column(db.Date)
    department_status = db.Column(db.String(80))
    special_case_status = db.Column(db.String(80))
    proposed_decision = db.Column(db.String(30))
    decision_status = db.Column(db.String(30))
    status = db.Column(db.String(10))
    status_reason = db.Column(db.String(30))
    submitted = db.Column(db.Date)
    withdrawn = db.Column(db.Date)
    admitted = db.Column(db.Date)
    deferred = db.Column(db.Date)
    enrolled = db.Column(db.Date)
    marked_complete = db.Column(db.Date)


class Target(db.Model):
    program_type = db.Column(
        db.String(10),
        ForeignKey("program_mapping.program_type"),
        primary_key=True,
        autoincrement=False,
    )
    year = db.Column(db.String(10), primary_key=True, autoincrement=False)
    fee_status = db.Column(db.String, primary_key=True, autoincrement=False)
    target = db.Column(db.Integer)


class ApplicantComment(db.Model):
    comment_id = db.Column(db.Integer, primary_key=True)
    erpid = db.Column(db.Integer)  # TODO Fix Foreign Key Relations
    username = db.Column(db.String)  # TODO Fix Foreign Key Relations
    timestamp = db.Column(db.DateTime, default=func.now())
    comment = db.Column(db.String)
