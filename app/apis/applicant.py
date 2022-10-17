from app import api
from app.database import db
from app.models.applicant import Applicant
from app.schemas.applicant import ApplicantSchema
from flask import request
from flask_restx import Resource


applicant_api = api.namespace("api/applicant", description="Applicant API")

applicant_deserializer = ApplicantSchema()


@applicant_api.route("/", methods=["GET"])
class ApplicantApi(Resource):
    def get(self):
        gender = request.args.get("gender", default=None, type=str)
        nationality = request.args.get("nationality", default=None, type=str)

        query = Applicant.query
        if gender is not None:
            query = query.filter(Applicant.gender.ilike(gender))

        if nationality is not None:
            query = query.filter(Applicant.nationality.ilike(nationality))

        data = [applicant_deserializer.dump(d) for d in query.all()]

        return data, 200
