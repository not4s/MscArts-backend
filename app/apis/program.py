from app import api
from app.database import db
from flask import request, abort
from flask_restx import Resource

# Database
from app.models.applicant import Program
from app.schemas.applicant import ProgramSchema

from app.apis.user import write_access_required

program_api = api.namespace("api/program", description="Program API")

program_data_serializer = ProgramSchema()


@program_api.route("/", methods=["GET", "POST", "PUT", "DELETE"])
class ProgramAPI(Resource):
    @write_access_required
    def get(self):
        data = Program.query.all()
        result = [program_data_serializer.dump(d) for d in data]
        return result, 200

    @write_access_required
    def post(self):
        if not request.is_json:
            abort(406, description="MIME type is required to be application/json.")

        body = request.json

        program_type = body.get("program_type", None)
        code = body.get("code", None)
        name = body.get("name", None)
        academic_level = body.get("academic_level", None)

        if (
            program_type is None
            or code is None
            or name is None
            or academic_level is None
        ):
            return {"message": "Malformed Request"}, 400

        program_type = program_type.strip()
        code = code.strip()
        name = name.strip()
        academic_level = academic_level.strip()

        new_program = Program(
            program_type=program_type,
            code=code,
            name=name,
            academic_level=academic_level,
        )
        db.session.add(new_program)
        db.session.commit()
        return {"message": "Added new program"}, 200

    @write_access_required
    def delete(self):
        if not request.is_json:
            abort(406, description="MIME type is required to be application/json.")

        body = request.json

        code = body.get("code", None)

        if code is None:
            return {"message": "Malformed Request"}, 400

        code = code.strip()
        program = Program.query.filter_by(code=code).first()

        if program is None:
            return {"message": "No program with the specified code"}, 400

        db.session.delete(program)
        db.session.commit()
        return {"message": "Program deleted"}, 200

    @write_access_required
    def put(self):
        if not request.is_json:
            abort(406, description="MIME type is required to be application/json.")

        body = request.json

        program_type = body.get("program_type", None)
        code = body.get("code", None)
        name = body.get("name", None)
        academic_level = body.get("academic_level", None)
        active = body.get("active", None)

        if (
            program_type is None
            or code is None
            or name is None
            or academic_level is None
            or active is None
        ):
            return {"message": "Malformed Request"}, 400

        program_type = program_type.strip()
        code = code.strip()
        name = name.strip()
        academic_level = academic_level.strip()

        program = Program.query.filter_by(code=code).first()

        if program is None:
            return {"message": "No program with the specified code"}, 400

        program.program_type = program_type
        program.name = name
        program.academic_level = academic_level
        program.active = active
        db.session.commit()
        return {"message": "Updated Program Activity"}, 200
