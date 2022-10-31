from app import db
from app.models.applicant import Applicant
from sqlalchemy.sql import func, and_

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

    query = Applicant.query

    query = query.join(
        latest_version,
        and_(
            latest_version.c.version == Applicant.version,
            latest_version.c.erpid == Applicant.erpid,
        ),
    )

    return query
