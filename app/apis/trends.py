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
      period = request.args.get("period", default="year", type=str).lower()
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

      today = date.today()

      if period == "year":
        old_date = today - relativedelta(years = unit)
      elif period == "month":
        old_date = today - relativedelta(months = unit)
      elif period == "week":
        old_date = today - relativedelta(weeks = unit)
      elif period == "day":
        old_date = today - relativedelta(days = unit)

      data_since_old_date = [applicant_deserializer.dump(d)["submitted"] for d in query.filter(Applicant.submitted > old_date)]
      data_since_old_date = list(map(lambda x : datetime.strptime(x, "%Y-%m-%d").date(), data_since_old_date))
      data = []
      if period == "year":
        data = split_into_year(unit, today, data_since_old_date)
      elif period == "month":
        data = split_into_month(unit, today, data_since_old_date)
      elif period == "week":
        data = split_into_week(unit, today, data_since_old_date)
      elif period == "day":
        data = split_into_day(unit, today, data_since_old_date)
      return data, 200

def all_year_data(query):
  years_data = [applicant_deserializer.dump(d) for d in db.session.query(Applicant.admissions_cycle).distinct()]
      
  data = []
  for year_data in years_data:
    year = year_data["admissions_cycle"]
    data.append({"period": year, "count": query.filter(Applicant.admissions_cycle == year).count()})
  
  return data
  

def split_into_year(unit, today, data_since_old_date):
  data = []
  upper_bound = today
  lower_bound = today - relativedelta(years = 1)
  while unit > 0:
    data.append({"period": (lower_bound + relativedelta(days = 1)).strftime("%m/%d/%Y"), 
    "count": len([x for x in data_since_old_date if x > lower_bound and x <= upper_bound])})
    upper_bound = lower_bound
    lower_bound = upper_bound - relativedelta(years = 1)
    unit -= 1

  return data

def split_into_month(unit, today, data_since_old_date):
  data = []
  upper_bound = today
  lower_bound = today - relativedelta(months = 1)
  while unit > 0:
    data.append({"period": (lower_bound + relativedelta(days = 1)).strftime("%m/%d/%Y"), 
    "count": len([x for x in data_since_old_date if x > lower_bound and x <= upper_bound])})
    upper_bound = lower_bound
    lower_bound = upper_bound - relativedelta(months = 1)
    unit -= 1

  return data

def split_into_week(unit, today, data_since_old_date):
  data = []
  upper_bound = today
  lower_bound = today - relativedelta(weeks = 1)
  while unit > 0:
    data.append({"period": (lower_bound + relativedelta(days = 1)).strftime("%m/%d/%Y"), 
    "count": len([x for x in data_since_old_date if x > lower_bound and x <= upper_bound])})
    upper_bound = lower_bound
    lower_bound = upper_bound - relativedelta(weeks = 1)
    unit -= 1

  return data

def split_into_day(unit, today, data_since_old_date):
  data = []
  date = today
  while unit > 0:
    data.append({"period": date.strftime("%m/%d/%Y"), 
    "count": len([x for x in data_since_old_date if x == date])})
    date = date - relativedelta(days = 1)
    unit -= 1

  return data