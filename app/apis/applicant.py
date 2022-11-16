from app import api
from app.database import db
from app.models.applicant import Applicant, Program
from app.schemas.applicant import ApplicantSchema
from app.apis.user import read_access_required
from app.utils.applicant import base_query
from flask import request, abort
from flask_restx import Resource
import pandas as pd

applicant_api = api.namespace("api/applicant", description="Applicant API")

applicant_deserializer = ApplicantSchema()

filters = [
    ("gender", str),
    ("nationality", str),
    ("program_code", str),
    ("erpid", int),
    ("combined_fee_status", str),
]

live = [
    "Condition Firm",
    "Condition Pending",
    "Uncondition Firm",
    "Uncondition Firm Temp",
    "Unconditional Firm Temp",
    "Uncondition Pending",
]

ETHNICITY_MAP = {
    "Arab": "Arab",
    "Asian - Bangladeshi": "Asian",
    "Asian - Chinese": "Chinese",
    "Asian - Indian": "Indian",
    "Asian - Other": "Asian",
    "Asian - Pakistani": "Asian",
    "Asian or Asian British - Bangladeshi": "Asian",
    "Asian or Asian British - Indian": "Indian",
    "Asian or Asian British - Pakistani": "Asian",
    "Black - African": "Black",
    "Black - Caribbean": "Black",
    "Black - Other": "Black",
    "Black or Black British - African": "Black",
    "Black or Black British - Caribbean": "Black",
    "Chinese": "Chinese",
    "Gypsy or Traveller": "Other/Unknown",
    "Mixed - Other": "Other/Unknown",
    "Mixed - White and Asian": "Asian",
    "Mixed - White and Black African": "Black",
    "Mixed - White and Black Caribbean": "Black",
    "Not known": "Other/Unknown",
    "Other": "Other/Unknown",
    "Other/Unknown": "Other/Unknown",
    "Other Asian background": "Asian",
    "Other Black background": "Black",
    "Other Mixed background": "Other/Unknown",
    "Other White background": "White",
    "Other ethnic background": "Other/Unknown",
    "Prefer not to say": "Other/Unknown",
    "Unknown": "Other/Unknown",
    "White": "White",
    "White - British": "White",
}


@applicant_api.route("/attribute", methods=["GET"])
class ApplicantAttributeApi(Resource):
    def get(self):

        data = {}
        for (col, col_type) in filters:
            data[col] = []
            for value in db.session.query(Applicant.__dict__[col]).distinct():
                data[col].append(applicant_deserializer.dump(value)[col])

        return data, 200


# def get_latest_version():
#     query = db.session.query(Applicant.erpid, func.max(Applicant.version).label('version')).group_by(Applicant.erpid)
#     return query.all()


@applicant_api.route("/", methods=["GET"])
class ApplicantApi(Resource):
    @read_access_required
    def get(self):
        query = base_query()

        program_type_filter = request.args.get("program_type", default=None, type=str)
        decision_status_filter = request.args.get(
            "decision_status", default=None, type=str
        )

        if program_type_filter is not None:
            query = query.join(Program, Applicant.program_code == Program.code)
            query = query.filter(Program.program_type == program_type_filter)

        if decision_status_filter == "live":
            # live applicants haven't been enrolled yet (they could still come)
            query = query.filter(
                Applicant.decision_status.in_(live), Applicant.enrolled.is_(None)
            )
            # TODO: cleared/paid/accepted
        elif decision_status_filter == "not_live":
            query = query.filter(Applicant.decision_status.notin_(live))

        for (col, col_type) in filters:
            filter_value = request.args.get(col, default=None, type=col_type)

            if filter_value is not None:
                if col_type is str:
                    query = query.filter(Applicant.__dict__[col].ilike(filter_value))
                elif col_type is int:
                    query = query.filter(Applicant.__dict__[col] == filter_value)

        # query = query.filter().group_by(Applicant.erpid)

        data = [applicant_deserializer.dump(d) for d in query.all()]

        if len(data) == 0:
            return data, 200

        count = request.args.get("count", default=None, type=str)
        series = request.args.get("series", default=None, type=str)

        if count and series:
            df = pd.DataFrame(data)
            counted = df[[count, series]].value_counts()
            print(counted)
            reformatted = []
            for key, value in counted.items():
                if key[0].strip() != "":
                    combined = list(
                        filter(
                            lambda x: x[count] == "Combined" and x["type"] == key[1],
                            reformatted,
                        )
                    )
                    if len(combined) > 0:
                        reformatted.remove(combined[0])
                        reformatted.append(
                            {
                                count: "Combined",
                                "count": int(value) + combined[0]["count"],
                                "type": key[1],
                            }
                        )
                    else:
                        reformatted.append(
                            {
                                count: "Combined",
                                "count": int(value),
                                "type": key[1],
                            }
                        )
                    reformatted.append(
                        {
                            count: key[0],
                            "count": int(value),
                            "type": key[1],
                        }
                    )
            reformatted = list(sorted(reformatted, key=lambda x: -x["count"]))
            return reformatted, 200

        if count:
            df = pd.DataFrame(data)
            counted = df[count].value_counts()
            reformatted = []
            for key, value in counted.items():
                if key.strip() != "":
                    reformatted.append(
                        {count: "Combined", "count": int(value), "type": key}
                    )
                    reformatted.append({count: key, "count": int(value), "type": key})
            return reformatted, 200
        return data, 200
