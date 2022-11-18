from app import db
from app.models.applicant import Applicant, Program
from app.schemas.applicant import ApplicantSchema
from sqlalchemy.sql import func, and_

applicant_deserializer = ApplicantSchema()

live = [
    "Condition Firm",
    "Condition Pending",
    "Uncondition Firm",
    "Uncondition Firm Temp",
    "Unconditional Firm Temp",
    "Uncondition Pending",
]


# Returns a query that only selects the latest version for each erpid
def base_query():
    latest_version = (
        db.session.query(
            Applicant.erpid.label("erpid"),
            func.max(Applicant.version).label("version"),
        )
        .group_by(Applicant.erpid)
        .subquery()
    )

    query = Applicant.query.join(
        latest_version,
        and_(
            latest_version.c.version == Applicant.version,
            latest_version.c.erpid == Applicant.erpid,
        ),
    )

    return query


# Filter down query and fetch applicants with the corresponding
# program_type and decision_status
def fetch_applicants(program_type, decision_status, custom_decision=None):
    query = base_query()

    query = query.join(Program, Applicant.program_code == Program.code)
    query = query.filter(Program.active == True)

    if program_type is not None and program_type != "ALL":
        query = query.filter(Program.program_type == program_type)

    if decision_status == "live":
        # live applicants haven't been enrolled yet (they could still come)
        query = query.filter(
            Applicant.decision_status.in_(live), Applicant.enrolled.is_(None)
        )
        # TODO: cleared/paid/accepted
    elif decision_status == "not_live":
        query = query.filter(Applicant.decision_status.notin_(live))
    elif decision_status == "custom" and custom_decision is not None:
        custom_decisions = custom_decision.split(",")
        query = query.filter(Applicant.decision_status.in_(custom_decisions))

    return [applicant_deserializer.dump(d) for d in query.all()]
