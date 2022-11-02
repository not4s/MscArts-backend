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
    ("fee_status", str),
]

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

        if program_type_filter is not None:
            query = query.join(Program, Applicant.program_code == Program.code)
            query = query.filter(Program.program_type == program_type_filter)

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
        series = request.args.get("series", default="application_status", type=str)

        if count and series:
            df = pd.DataFrame(data)
            counted = df[[count, series]].value_counts()
            reformatted = []
            for key, value in counted.items():
                if key[0].strip() != "":
                    combined = list(
                        filter(
                            lambda x: x[count] == "Combined" and x["series"] == key[1],
                            reformatted,
                        )
                    )
                    if len(combined) > 0:
                        reformatted.remove(combined[0])
                        reformatted.append(
                            {
                                count: "Combined",
                                "count": int(value) + combined[0]["count"],
                                "type": key[0],
                                "series": key[1],
                            }
                        )
                    else:
                        reformatted.append(
                            {
                                count: "Combined",
                                "count": int(value),
                                "type": key[0],
                                "series": key[1],
                            }
                        )
                    reformatted.append(
                        {
                            count: key[0],
                            "count": int(value),
                            "type": key[0],
                            "series": key[1],
                        }
                    )
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
