from app import api
from app.database import db
from app.models.applicant import Applicant, Program, ApplicantComment
from app.schemas.applicant import ApplicantSchema, ApplicantCommentSchema
from app.apis.user import read_access_required, write_access_required
from app.utils.applicant import base_query, fetch_applicants
from app.utils.graph import applicants_to_bar, applicants_to_pie
from flask_jwt_extended import get_jwt
from flask import request, abort
from flask_restx import Resource
from sqlalchemy import desc
import pandas as pd

applicant_api = api.namespace("api/applicant", description="Applicant API")

applicant_deserializer = ApplicantSchema()
applicant_comment_deserializer = ApplicantCommentSchema()

filters = [
    ("gender", str),
    ("nationality", str),
    ("program_code", str),
    ("erpid", int),
    ("combined_fee_status", str),
    ("admissions_cycle", int),
]


@applicant_api.route("/attribute/", methods=["GET"])
class ApplicantAttributeApi(Resource):
    def get(self):

        data = {}
        for (col, col_type) in filters:
            data[col] = []
            for value in db.session.query(Applicant.__dict__[col]).distinct():
                data[col].append(applicant_deserializer.dump(value)[col])
            if col == "admissions_cycle":
                data[col] = [d for d in data[col] if d > 0]

        return data, 200


@applicant_api.route("/", methods=["GET"])
class ApplicantApi(Resource):
    @read_access_required
    def get(self):
        year = request.args.get("year", default=None, type=int)
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
            program_type_filter, decision_status_filter, custom_decision, year, username
        )

        if len(data) == 0:
            return data, 200

        return data, 200


@applicant_api.route("/graph/", methods=["GET"])
class ApplicantApi(Resource):
    @read_access_required
    def get(self):
        graph_type = request.args.get("type", default=None, type=str)
        primary_type = request.args.get("primary", default=None, type=str)
        year = request.args.get("year", default=None, type=int)

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
            program_type_filter, decision_status_filter, custom_decision, year, username
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


@applicant_api.route("/comment/", methods=["GET", "POST"])
class ApplicantCommentAPI(Resource):
    @write_access_required
    def get(self):
        erpid = request.args.get("erpid", default=None, type=int)

        if erpid is None:
            return [], 200

        query = ApplicantComment.query.filter_by(erpid=erpid).order_by(
            desc(ApplicantComment.timestamp)
        )

        return [applicant_comment_deserializer.dump(d) for d in query.all()], 200

    @write_access_required
    def post(self):
        if not request.is_json:
            abort(406, description="MIME type is required to be application/json.")

        body = request.json

        comment = body.get("comment", None)
        erpid = body.get("erpid", None)
        username = get_jwt()["sub"]["username"]

        if erpid is None or comment is None:
            return {"message": "Malformed Request"}, 400

        newComment = ApplicantComment(erpid=erpid, username=username, comment=comment)

        db.session.add(newComment)
        db.session.commit()
        return {"message": "Added new comment"}, 200
