from app import api
from app.database import db
from app.models.applicant import Applicant, Target
from app.schemas.applicant import ApplicantSchema, TargetSchema
from app.apis.user import read_access_required
from flask import request, abort
from flask_restx import Resource
import pandas as pd
import random

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


@applicant_api.route("/target", methods=["GET", "POST", "PUT"])
class ApplicantApi(Resource):
    def get(self):
        program_type = request.args.get("type", default=None, type=str)
        year = request.args.get("year", default=None, type=str)
        query = db.session.query(Target)
        if program_type is not None:
            query = query.filter_by(program_type=program_type)
        if year is not None:
            query = query.filter_by(year=year)

        data = [target_deserializer.dump(d) for d in query.all()]

        # TODO: track the progress
        for i, target in enumerate(data):
            data[i] = {**target, "progress" : random.randint(1, 100)}
        
        return data, 200

    def post(self):
        if not request.is_json:
            abort(406, description="MIME type is required to be application/json.")

        body = request.json

        program_type = body.get("program_type", None)
        year = body.get("year", None)
        target = body.get("target", None)

        if program_type is None or year is None or target is None:
            return {"message": "Malformed Request"}, 400

        program_type = program_type.strip()

        new_target = Target(program_type=program_type, year=year, target=target)
        db.session.add(new_target)
        db.session.commit()

        # program_type=request.args.get("type", default=None, type=str)
        # year = request.args.get("year", default=None, type=str)
        # target = request.args.get("target", default=None, type=int)

        # db.session.add(Target(program_type=program_type, year=year, target=target))
        # db.session.commit()

        return {"message": "Uploaded Target"}, 200

    def put(self):
        if not request.is_json:
            abort(406, description="MIME type is required to be application/json.")

        body = request.json

        program_type = body.get("program_type", None)
        year = body.get("year", None)
        target_num = body.get("target", None)

        if program_type is None or year is None or target_num is None:
            return {"message": "Malformed Request"}, 400

        program_type = program_type.strip()

        target = Target.query.filter_by(program_type=program_type, year=year).first()

        if target is None:
            return {"message": "No program with the specified code"}, 400

        target.program_type = program_type
        target.year = year
        target.target = target_num
        db.session.commit()
        return {"message": "Updated Target"}, 200


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
