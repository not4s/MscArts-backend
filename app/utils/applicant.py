from app import db
from app.models.applicant import Applicant, Program
from app.schemas.applicant import ApplicantSchema
from app.schemas.applicant import ProgramSchema
from app.utils.mock_cache import mock_cache
from sqlalchemy.sql import func, and_

applicant_deserializer = ApplicantSchema()
program_deserializer = ProgramSchema()

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
def fetch_applicants(
    program_type, decision_status, custom_decision=None, year=None, username=None
):
    if username is not None:
        return mock_cache.get(username)

    query = base_query()

    query = query.join(Program, Applicant.program_code == Program.code)
    query = query.filter(Program.active == True)

    if year is not None:
        query = query.filter(Applicant.admissions_cycle == year)

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

    data = []
    prog_dict = {}

    for d in Program.query.all():
        prog_dict[d.code] = d.program_type


    for d in query.all():
        deserialized = applicant_deserializer.dump(d)
        deserialized['program_type'] = prog_dict[deserialized['program_code']]
        data.append(deserialized)

    return data