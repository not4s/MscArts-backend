import enum
from app.database import db
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
    erpid = db.Column(db.Integer, primary_key=True)
    prefix = db.Column(db.String(10))
    first_name = db.Column(db.String(80))
    last_name = db.Column(db.String(80))
    gender = db.Column(db.String)
    nationality = db.Column(db.String(100))
    email = db.Column(db.String(120))
    fee_status = db.Column(db.String(20))
    program_code = db.Column(db.String(10), ForeignKey("program.code"))
    application_status = db.Column(db.String(80))
    supplemental_complete = db.Column(db.Boolean)
    academic_eligibility = db.Column(db.String(80))
    folder_status = db.Column(db.String(80))
    date_to_department = db.Column(db.Date)
    department_status = db.Column(db.String(80))
    special_case_status = db.Column(db.String(80))
    proposed_decision = db.Column(db.String(30))
    submitted = db.Column(db.Date)
    marked_complete = db.Column(db.Date)

class Target(db.Model):
    program_type = db.Column(db.String(10), ForeignKey('program_mapping.program_type'), primary_key=True, autoincrement=False)
    year = db.Column(db.String(10), primary_key=True, autoincrement=False)
    target = db.Column(db.Integer)
