from app import api
from app.database import db
from app.models.applicant import Applicant
from app.schemas.applicant import ApplicantSchema
from flask import request
from flask_restx import Resource


applicant_api = api.namespace("api/applicant", description="Applicant API")

applicant_deserializer = ApplicantSchema()

filters = [
    ("gender", str),
    ("nationality", str),
    ("program_code", str),
    ("erpid", int),
    ("fee_status", str),
]


@applicant_api.route("/", methods=["GET"])
class ApplicantApi(Resource):
    def get(self):
        query = Applicant.query

        for (col, col_type) in filters:
            filter_value = request.args.get(col, default=None, type=col_type)

            if filter_value is not None:
                if col_type is str:
                    query = query.filter(Applicant.__dict__[col].ilike(filter_value))
                elif col_type is int:
                    query = query.filter(Applicant.__dict__[col] == filter_value)

        data = [applicant_deserializer.dump(d) for d in query.all()]
        return data, 200
