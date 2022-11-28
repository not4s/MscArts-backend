from app import api
from app.database import db
from app.models.applicant import Applicant, Program
from app.schemas.applicant import ApplicantSchema, ProgramSchema
from app.utils.applicant import base_query
from flask import request
from flask_restx import Resource
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

trends_api = api.namespace("api/trends", description="Trends API")

applicant_deserializer = ApplicantSchema()
program_deserializer = ProgramSchema()
periods = ["day", "week", "month", "year"]

@trends_api.route("/", methods=["GET"])
class TrendsApi(Resource):
    def get(self):
      query = base_query()

      unit = request.args.get("unit", type=int)
      period = request.args.get("period", default="year", type=str).lower()
      series = request.args.get("series", default=None, type=str)
      program_code = request.args.get("code", default=None, type=str)
      gender = request.args.get("gender", default=None, type=str)
      fee_status = request.args.get("fee_status", default=None, type=str)
      nationality = request.args.get("nationality", default=None, type=str)
      decision_status = request.args.get("decision_status", default=None, type=str)

      if decision_status is not None and decision_status.lower() != "all":
        query = query.filter(Applicant.decision_status == decision_status)
        
      if program_code is not None and program_code.lower() != "all":
        program_codes = [program_deserializer.dump(d)['code'] for d in db.session.query(Program).filter(Program.program_type == program_code)]
        print(program_codes)
        query = query.filter(Applicant.program_code.in_(program_codes))
      
      if not series:
        if gender is not None:
          query = query.filter(Applicant.gender == gender)

        if fee_status is not None:
          query = query.filter(Applicant.combined_fee_status == fee_status)

        if nationality is not None:
          query = query.filter(Applicant.nationality == nationality)
        
      
      if not unit:
        # return all years data
        return all_year_data(query, series), 200

      today = date.today()

      if period == "year":
        old_date = today - relativedelta(years = unit)
      elif period == "month":
        old_date = today - relativedelta(months = unit)
      elif period == "week":
        old_date = today - relativedelta(weeks = unit)
      elif period == "day":
        old_date = today - relativedelta(days = unit)

      applicants = [applicant_deserializer.dump(d) for d in query.filter(Applicant.submitted > old_date)]      
      if series:
        applicants = list(map(lambda x: {'submitted': datetime.strptime(x['submitted'], "%Y-%m-%d").date(), 'series': x[series]}, applicants))
        series = set([applicant_deserializer.dump(d)[series] for d in db.session.query(Applicant)])
      else:
        applicants = list(map(lambda x: {'submitted': datetime.strptime(x['submitted'], "%Y-%m-%d").date(), 'series': 'ALL'}, applicants))
        series = set(['ALL'])

      data = []
      if period == "year":
        data = split_into_year(unit, today, applicants, series)
      elif period == "month":
        data = split_into_month(unit, today, applicants, series)
      elif period == "week":
        data = split_into_week(unit, today, applicants, series)
      elif period == "day":
        data = split_into_day(unit, today, applicants, series)
      return data, 200

def all_year_data(query, series):
  years_data = [applicant_deserializer.dump(d) for d in db.session.query(Applicant.admissions_cycle).distinct()]
  if series is not None:
    series_data = [applicant_deserializer.dump(d) for d in db.session.query(Applicant.gender).distinct()]
  data = []
  for year_data in years_data:
    year = year_data["admissions_cycle"]
    if series:
      for s in series_data:
        series = s["gender"]
        data.append({"period": year, "series": series, "count": query.filter(Applicant.admissions_cycle == year, Applicant.gender == series).count()})
    else:
        data.append({"period": year, "count": query.filter(Applicant.admissions_cycle == year).count()})
  
  return data
  

def split_into_year(unit, today, data_since_old_date, series):
  data = []
  upper_bound = today
  lower_bound = today - relativedelta(years = 1)
  while unit > 0:
    for s in series:
      data.append({"period": (lower_bound + relativedelta(days = 1)).strftime("%m/%d/%Y"), 
      "series": s,
      "count": len([x for x in data_since_old_date if x['submitted'] > lower_bound and x['submitted'] <= upper_bound and x['series'] == s])})
    upper_bound = lower_bound
    lower_bound = upper_bound - relativedelta(years = 1)
    unit -= 1

  return data

def split_into_month(unit, today, data_since_old_date, series, upper_bound_inclusive=True):
  data = []
  upper_bound = today
  lower_bound = today - relativedelta(months = 1)
  while unit > 0:
    for s in series:
      if (upper_bound_inclusive):
        count = len([x for x in data_since_old_date if x['submitted'] > lower_bound and x['submitted'] <= upper_bound and x['series'] == s])
        period = (lower_bound + relativedelta(days = 1)).strftime("%m/%d/%Y")
      else:
        count = len([x for x in data_since_old_date if x['submitted'] >= lower_bound and x['submitted'] < upper_bound and x['series'] == s])
        period = lower_bound.strftime("%m/%d/%Y")
      data.append({"period": period, 
      "series": s,
      "count": count})
    print("Upper bound (inclusive)", upper_bound)
    print("Lower bound (exclusive)", lower_bound)
    upper_bound = lower_bound
    lower_bound = upper_bound - relativedelta(months = 1)
    unit -= 1

  return data

def split_into_week(unit, today, data_since_old_date, series, upper_bound_inclusive=True):
  data = []
  upper_bound = today
  lower_bound = today - relativedelta(weeks = 1)
  while unit > 0:
    for s in series:
      if upper_bound_inclusive:
        count = len([x for x in data_since_old_date if x['submitted'] > lower_bound and x['submitted'] <= upper_bound and x['series'] == s])
        period = (lower_bound + relativedelta(days = 1)).strftime("%m/%d/%Y")
      else:
        count = len([x for x in data_since_old_date if x['submitted'] >= lower_bound and x['submitted'] < upper_bound and x['series'] == s])
        period = lower_bound.strftime("%m/%d/%Y")
      data.append({"period": period, 
      "series": s,
      "count": count})
    upper_bound = lower_bound
    lower_bound = upper_bound - relativedelta(weeks = 1)
    unit -= 1

  return data

def split_into_day(unit, today, data_since_old_date, series):
  data = []
  date = today
  while unit > 0:
    for s in series:
      data.append({"period": date.strftime("%m/%d/%Y"), 
      "count": len([x for x in data_since_old_date if x['submitted'] == date and x['series'] == s])})
    date = date - relativedelta(days = 1)
    unit -= 1

  return data

# for each "cycle", get all the data between start and end month for each period
@trends_api.route("/cycle", methods=["GET"])
class TrendsCycleApi(Resource):
    def get(self):
      query = base_query()

      unit = request.args.get("unit", type=int)
      period = request.args.get("period", default="year", type=str).lower()
      cycles = request.args.get("cycle", default=None, type=str) # e.g. cycle=21,22,23
      cumulative = request.args.get("cumulative", default=True, type=bool)
      start =request.args.get("start", default=10, type=int)
      end = request.args.get("end", default=10, type=int)
      series = request.args.get("series", default=None, type=str)
      program_code = request.args.get("code", default=None, type=str)
      gender = request.args.get("gender", default=None, type=str)
      fee_status = request.args.get("fee_status", default=None, type=str)
      nationality = request.args.get("nationality", default=None, type=str)

      if start < 10 and end > 10 or start > 10 and end == start:
        return {"message": "Invalid time frame given"}, 400

      if not series:
        if program_code is not None:
          query = query.filter(Applicant.program_code == program_code)
        
        if gender is not None:
          query = query.filter(Applicant.gender == gender)

        if fee_status is not None:
          query = query.filter(Applicant.combined_fee_status == fee_status)

        if nationality is not None:
          query = query.filter(Applicant.nationality == nationality)
      
      cycles = cycles.split(",")
      cycles = ["20" + cycle for cycle in cycles]
      data = []

      if series:
        series_types = set([applicant_deserializer.dump(d)[series] for d in db.session.query(Applicant)])
      else:
        series_types = set(['ALL'])
      print(series_types)
      for cycle in cycles:
        print(f"---------{cycle}--------")
        applicants = [applicant_deserializer.dump(d) for d in query.filter(Applicant.admissions_cycle == int(cycle))]
        print("got", len(applicants), "applicants from database")
        if series:
          applicants = list(map(lambda x: {'submitted': datetime.strptime(x['submitted'], "%Y-%m-%d").date(), 'series': x[series]}, applicants))
        else:
          applicants = list(map(lambda x: {'submitted': datetime.strptime(x['submitted'], "%Y-%m-%d").date(), 'series': 'ALL'}, applicants))
        print(applicants)

        # get "today's" date
        if end > 10:
          today = date(int(cycle), end, 1)
        else:
          today = date(int(cycle) + 1, end, 1)
        
        # get the "start" date
        if start >= 10:
          start_date = date(int(cycle), start, 1)
        else:
          start_date = date(int(cycle) + 1, start)
        
        if period == "month":
          unit = (today.year - start_date.year) * 12 + today.month - start_date.month + 1
        elif period == "week":
          unit = abs(today - start_date).days // 7 + 1
        elif period == "day":
          unit = abs(today - start_date).days

        print("Today's date:", today)
        print("Oldest possible entry", start_date)
        print("Going back", unit, period)

        print(len(applicants))
        if period == "month":
          new_data = split_into_month(unit, today, applicants, series_types, upper_bound_inclusive=False)
        elif period == "week":
          new_data = split_into_week(unit, today, applicants, series_types, upper_bound_inclusive=False)
        elif period == "day":
          new_data = split_into_day(unit, today, applicants, series_types)
        
        for d in new_data:
          d["series"] = cycle
          data.append(d)
      return data, 200
      