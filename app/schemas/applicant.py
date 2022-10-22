from app import ma
from app.models.applicant import Program, Applicant


class ProgramSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Program


class ApplicantSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Applicant
        include_fk = True
