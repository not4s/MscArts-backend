import enum
from app.database import db
from sqlalchemy import ForeignKey


class Program(db.Model):
    code = db.Column(db.String(10), primary_key=True, unique=True, autoincrement=False)
    name = db.Column(db.String(120))
    application_type = db.Column(db.String(120))


class Applicant(db.Model):
    erpid = db.Column(db.Integer, primary_key=True)
    prefix = db.Column(db.String(10))
    first_name = db.Column(db.String(80))
    last_name = db.Column(db.String(80))
    gender = db.Column(db.String)
    nationality = db.Column(db.String(100))
    email = db.Column(db.String(120))
    fee_status = db.Column(db.String(20))
    program_code = db.Column(db.String(10), ForeignKey("program.code"))


class ApplicantStatus(db.Model):
    id = db.Column(db.Integer, ForeignKey("applicant.erpid"), primary_key=True)
    status = db.Column(db.String(80))
    supplemental_complete = db.Column(db.Boolean)
    academic_eligibility = db.Column(db.String(80))
    folder_status = db.Column(db.String(80))
    date_to_department = db.Column(db.Date)
    department_status = db.Column(db.String(80))
    special_case_status = db.Column(db.String(80))
    proposed_decision = db.Column(db.String(30))
    submitted = db.Column(db.Date)
    marked_complete = db.Column(db.Date)
