from app import ma
from app.models.applicant import (
    Program,
    Applicant,
    Target,
    ProgramMapping,
    ApplicantComment,
)


class ProgramSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Program
        include_fk = True


class ProgramMappingSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ProgramMapping


class ApplicantSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Applicant
        include_fk = True


class TargetSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Target
        include_fk = True


class ApplicantCommentSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ApplicantComment
