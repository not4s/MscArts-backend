import pandas as pd
from app import api
from app.database import db
from app.models.applicant import Applicant, Target, Program
from app.schemas.applicant import ApplicantSchema, TargetSchema
from app.utils.applicant import base_query, fetch_applicants
from flask import request, abort
from flask_restx import Resource

target_api = api.namespace("api/target", description="Target API")

target_deserializer = TargetSchema()

applicant_deserializer = ApplicantSchema()

live = [
    "Condition Firm",
    "Condition Pending",
    "Uncondition Firm",
    "Uncondition Firm Temp",
    "Unconditional Firm Temp",
    "Uncondition Pending",
]


@target_api.route("/progress/", methods=["GET"])
class TargetProgressApi(Resource):
    def get(self):
        program_type = request.args.get("type", default=None, type=str)
        year = request.args.get("year", default=None, type=str)
        query = db.session.query(Target)
        if program_type is not None:
            query = query.filter_by(program_type=program_type)
        if year is not None:
            query = query.filter_by(year=year)

        data = [target_deserializer.dump(d) for d in query.all()]

        applicants = fetch_applicants(None, "custom", ",".join(live))
        df = pd.DataFrame(applicants)
        df = df[["program_type", "admissions_cycle", "combined_fee_status"]].value_counts()

        for i, target in enumerate(data):
            print(data[i])
            data[i]['progress'] = int(df[(target['program_type'], int(target['year']), target['fee_status'])])

        print(data)
        return data, 200


@target_api.route("/", methods=["GET", "POST", "PUT", "DELETE"])
class TargetApi(Resource):
    def get(self):
        program_type = request.args.get("program_type", default=None, type=str)
        year = request.args.get("year", default=None, type=str)

        query = Target.query

        if program_type is not None:
            query = query.filter_by(program_type=program_type)

        if year is not None:
            query = query.filter_by(year=year)

        return [target_deserializer.dump(d) for d in query.all()], 200

    def post(self):
        if not request.is_json:
            abort(406, description="MIME type is required to be application/json.")

        body = request.json

        program_type = body.get("program_type", None)
        year = body.get("year", None)
        fee_status = body.get("fee_status", None)
        target = body.get("target", None)

        if program_type is None or year is None or fee_status is None or target is None:
            return {"message": "Malformed Request"}, 400

        program_type = program_type.strip()
        fee_status = fee_status.strip()

        try:
            new_target = Target(
                program_type=program_type,
                year=year,
                fee_status=fee_status,
                target=target,
            )
            db.session.add(new_target)
            db.session.commit()
        except:
            return {"message": "Exists"}, 200

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
        fee_status = body.get("fee_status", None)
        target_num = body.get("target", None)

        if (
            program_type is None
            or year is None
            or target_num is None
            or fee_status is None
        ):
            return {"message": "Malformed Request"}, 400

        program_type = program_type.strip()
        fee_status = fee_status.strip()

        target = Target.query.filter_by(
            program_type=program_type, fee_status=fee_status, year=year
        ).first()

        if target is None:
            return {"message": "No program with the specified code"}, 400

        target.program_type = program_type
        target.year = year
        target.target = target_num
        db.session.commit()
        return {"message": "Updated Target"}, 200

    def delete(self):
        if not request.is_json:
            abort(406, description="MIME type is required to be application/json.")

        body = request.json

        program_type = body.get("program_type", None)
        year = body.get("year", None)
        fee_status = body.get("fee_status", None)

        if program_type is None or year is None or fee_status is None:
            return {"message": "Malformed Request"}, 400

        program_type = program_type.strip()
        try:
            Target.query.filter_by(
                program_type=program_type, year=year, fee_status=fee_status
            ).delete()
            db.session.commit()
            return {"message": "Deleted"}, 200
        except Exception as e:
            return {"message": "Could not delete"}, 200
