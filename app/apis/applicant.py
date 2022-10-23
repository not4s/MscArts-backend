from app import api
from app.database import db
from app.models.applicant import Applicant, Target
from app.schemas.applicant import ApplicantSchema, TargetSchema
from app.apis.user import read_access_required
from flask import request
from flask_restx import Resource
import pandas as pd


applicant_api = api.namespace("api/applicant", description="Applicant API")

applicant_deserializer = ApplicantSchema()

target_deserializer = TargetSchema()

filters = [
    ("gender", str),
    ("nationality", str),
    ("program_code", str),
    ("erpid", int),
    ("fee_status", str),
]


@applicant_api.route("/target", methods=["GET", "POST"])
class ApplicantApi(Resource):
    def get(self):
        course = request.args.get("course", default=None, type=str)
        year = request.args.get("year", default=None, type=str)

        data = target_deserializer.dump(db.session.query(Target).filter_by(program_code=course, year=year).one())

        # TODO: track the progress
        data = {**data, "progress" : 87.7}
        print(course)
        print(year)
        print(data)

        return data, 200

    def post(self):
        course=request.args.get("course", default=None, type=str)
        year = request.args.get("year", default=None, type=str)
        target = request.args.get("target", default=None, type=int)

        db.session.add(Target(program_code=course, year=year, target=target))
        db.session.commit()

        data = {"message": "target uploaded"}
        return data, 200

@applicant_api.route("/", methods=["GET"])
class ApplicantApi(Resource):
    @read_access_required
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

        if len(data) == 0:
            return data, 200

        count = request.args.get("count", default=None, type=str)
        if count:
            df = pd.DataFrame(data)
            counted = df[count].value_counts()
            reformatted = []
            for key, value in counted.items():
                if (key.strip() != ""):
                    reformatted.append(
                        {count: "Combined", "count": int(value), "type": key}
                    )
                    reformatted.append({count: key, "count": int(value), "type": key})
            return reformatted, 200
        return data, 200
