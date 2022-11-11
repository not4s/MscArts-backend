from app import api
from app.database import db
from app.models.applicant import Applicant, Program
from app.schemas.applicant import ApplicantSchema
from app.apis.user import read_access_required
from app.utils.applicant import base_query
from flask import request, abort
from flask_restx import Resource
import pandas as pd

trends_api = api.namespace("api/trends", description="Trends API")

applicant_deserializer = ApplicantSchema()


@trends_api.route("/", methods=["GET", "POST", "PUT", "DELETE"])
class TrendsApi(Resource):
    def get(self):
      query = base_query()

      # get all the years
      years_data = [applicant_deserializer.dump(d) for d in db.session.query(Applicant.admissions_cycle).distinct()]
      
      data = []
      for year_data in years_data:
        year = year_data["admissions_cycle"]
        data.append({"year": year, "count": query.filter(Applicant.admissions_cycle == year).count()})
      
      return data, 200