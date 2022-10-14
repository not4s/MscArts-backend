from app import api
from app.database import db 
from flask import request, abort
from flask_restx import Resource

# Database
from app.models.applicant import Program
from app.schemas.applicant import ProgramSchema

program_api = api.namespace("program", description="Program API")

program_data_serializer = ProgramSchema()

@program_api.route('/', methods=['GET'])
class ProgramAPI(Resource):
    def get(self):
        data = Program.query.all()
        result = [program_data_serializer.dump(d) for d in data]
        return result, 200
