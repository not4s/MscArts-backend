from app import ma
from app.models.applicant import Program, Applicant, ApplicantStatus

class ProgramSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Program

class ApplicantSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Applicant

class ApplicantStatusSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ApplicantStatus