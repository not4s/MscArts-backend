from app import api
from app.database import db
from app.models.applicant import Applicant, Target, Program
from app.schemas.applicant import ApplicantSchema, TargetSchema
from app.utils.applicant import base_query
from flask import request, abort
from flask_restx import Resource

target_api = api.namespace("api/target", description="Applicant API")

target_deserializer = TargetSchema()

applicant_deserializer = ApplicantSchema()

live = ['Condition Firm',
        'Condition Pending',
        'Uncondition Firm',
        'Uncondition Firm Temp',
        'Unconditional Firm Temp',
        'Uncondition Pending']

@target_api.route("/", methods=["GET", "POST", "PUT", "DELETE"])
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

        for i, target in enumerate(data):
            query = base_query()
            query = query.join(Program, Applicant.program_code == Program.code)
            query = query.filter(Program.program_type == target['program_type'], 
                                 Applicant.admissions_cycle == target['year'],
                                 Applicant.decision_status.in_(live))
            data[i] = {**target, "progress": query.count()}

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

        try:
            new_target = Target(program_type=program_type, year=year, target=target)
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

    def delete(self):
        if not request.is_json:
            abort(406, description="MIME type is required to be application/json.")

        body = request.json

        program_type = body.get("program_type", None)
        year = body.get("year", None)
        
        if program_type is None or year is None:
            return {"message": "Malformed Request"}, 400

        program_type = program_type.strip()
        try:
            Target.query.filter_by(program_type=program_type,year=year).delete()
            db.session.commit()
            return {"message": "Deleted"}, 200
        except Exception as e:
            return {"message": "Could not delete"}, 200