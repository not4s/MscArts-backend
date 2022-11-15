from app import api
from app.database import db
from app.models.applicant import Applicant
from app.schemas.applicant import ApplicantSchema
from app.utils.applicant import base_query
from flask import request
from flask_restx import Resource
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import pandas as pd

trends_api = api.namespace("api/trends", description="Trends API")

applicant_deserializer = ApplicantSchema()

periods = ["day", "week", "month", "year"]

@trends_api.route("/", methods=["GET", "POST", "PUT", "DELETE"])
class TrendsApi(Resource):
    def get(self):
      query = base_query()

      unit = request.args.get("unit", type=int)
      period = request.args.get("period", default="year", type=str)
      program_code = request.args.get("code", default=None, type=str)
      gender = request.args.get("gender", default=None, type=str)
      fee_status = request.args.get("fee_status", default=None, type=str)
      nationality = request.args.get("nationality", default=None, type=str)

      if program_code is not None:
        query = query.filter(Applicant.program_code == program_code)
      
      if gender is not None:
        query = query.filter(Applicant.gender == gender)

      if fee_status is not None:
        query = query.filter(Applicant.combined_fee_status == fee_status)

      if nationality is not None:
        query = query.filter(Applicant.nationality == nationality)
      
      if not unit:
        # return all years data
        return all_year_data(query), 200

      today = date(2022, 7, 31)

      data = []
      if period == "year":
        data = split_into_year(unit, today, query)
      elif period == "month":
        data = split_into_month(unit, today, query)
      elif period == "week":
        data = split_into_week(unit, today, query)
      elif period == "day":
        data = split_into_day(unit, today, query)
      return data, 200

def all_year_data(query):
  years_data = [applicant_deserializer.dump(d) for d in db.session.query(Applicant.admissions_cycle).distinct()]
      
  data = []
  for year_data in years_data:
    year = year_data["admissions_cycle"]
    data.append({"year": year, "count": query.filter(Applicant.admissions_cycle == year).count()})
  
  return data
  

def split_into_year(unit, today, query):
  data = []
  upper_bound = today
  lower_bound = today - relativedelta(years = 1)
  while unit > 0:
    data.append({"year": (lower_bound + relativedelta(days = 1)).strftime("%m/%d/%Y"), "count": query.filter(Applicant.submitted > lower_bound, Applicant.submitted <= upper_bound).count()})
    upper_bound = lower_bound
    lower_bound = upper_bound - relativedelta(years = 1)
    unit -= 1

  return data

def split_into_month(unit, today, query):
  data = []
  upper_bound = today
  lower_bound = today - relativedelta(months = 1)
  while unit > 0:
    data.append({"month": (lower_bound + relativedelta(days = 1)).strftime("%m/%d/%Y"), "count": query.filter(Applicant.submitted > lower_bound, Applicant.submitted <= upper_bound).count()})
    upper_bound = lower_bound
    lower_bound = upper_bound - relativedelta(months = 1)
    unit -= 1

  return data

def split_into_week(unit, today, query):
  data = []
  upper_bound = today
  lower_bound = today - relativedelta(weeks = 1)
  while unit > 0:
    data.append({"week": (lower_bound + relativedelta(days = 1)).strftime("%m/%d/%Y"), "count": query.filter(Applicant.submitted > lower_bound, Applicant.submitted <= upper_bound).count()})
    upper_bound = lower_bound
    lower_bound = upper_bound - relativedelta(weeks = 1)
    unit -= 1

  return data

def split_into_day(unit, today, query):
  data = []
  date = today
  while unit > 0:
    count = query.filter(Applicant.submitted == date).count()
    print(date, count)
    data.append({"day": date.strftime("%m/%d/%Y"), "count": count})
    date = date - relativedelta(days = 1)
    unit -= 1

  return data