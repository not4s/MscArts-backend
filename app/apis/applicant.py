from app import api
from app.database import db
from app.models.applicant import Applicant, Program
from app.schemas.applicant import ApplicantSchema
from app.apis.user import read_access_required
from app.utils.applicant import base_query, fetch_applicants
from app.utils.graph import applicants_to_bar, applicants_to_pie
from flask_jwt_extended import get_jwt
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


@applicant_api.route("/attribute", methods=["GET"])
class ApplicantAttributeApi(Resource):
    def get(self):

        data = {}
        for (col, col_type) in filters:
            data[col] = []
            for value in db.session.query(Applicant.__dict__[col]).distinct():
                data[col].append(applicant_deserializer.dump(value)[col])

        return data, 200


@applicant_api.route("/", methods=["GET"])
class ApplicantApi(Resource):
    @read_access_required
    def get(self):
        query = base_query()

        program_type_filter = request.args.get("program_type", default=None, type=str)
        decision_status_filter = request.args.get(
            "decision_status", default=None, type=str
        )

        query = query.join(Program, Applicant.program_code == Program.code)
        query = query.filter(Program.active == True)

        if program_type_filter is not None:
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
        print(query)

        data = [applicant_deserializer.dump(d) for d in query.all()]

        if len(data) == 0:
            return data, 200

        count = request.args.get("count", default=None, type=str)
        series = request.args.get("series", default=None, type=str)

        if count and series:
            df = pd.DataFrame(data)
            counted = df[[count, series]].value_counts()
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


@applicant_api.route("/graph/", methods=["GET"])
class ApplicantApi(Resource):
    @read_access_required
    def get(self):
        graph_type = request.args.get("type", default=None, type=str)
        primary_type = request.args.get("primary", default=None, type=str)

        if graph_type is None or primary_type is None:
            return {"message": "Malformed Request"}, 400

        program_type_filter = request.args.get("program_type", default=None, type=str)
        decision_status_filter = request.args.get(
            "decision_status", default="", type=str
        )
        custom_decision = request.args.get("custom_decision", default=None, type=str)
        mock = request.args.get("mock", default=None)

        username = None

        if mock is not None:
            username = get_jwt()["sub"]["username"]

        data = fetch_applicants(
            program_type_filter, decision_status_filter, custom_decision, username
        )

        if len(data) == 0:
            return data, 200

        if graph_type == "BAR":
            secondary_type = request.args.get("secondary", default=None, type=str)
            combined = request.args.get("combined", default=None)
            return applicants_to_bar(data, primary_type, secondary_type, combined), 200
        elif graph_type == "PIE":
            top = request.args.get("top", default=0, type=int)
            return applicants_to_pie(data, primary_type, top), 200
        elif graph_type == "LINE":
            return data, 200
        else:
            return {"message": "Unrecognized Graph Type"}, 400
