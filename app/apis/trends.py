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

admission_cycle_start = date(2022, 10, 1)
admissions_cycle_end = date(2023, 7, 31)

@trends_api.route("/", methods=["GET"])
class TrendsApi(Resource):
    def get(self):
      query = base_query()

      unit = request.args.get("unit", type=int)
      period = request.args.get("period", default="year", type=str).lower()
      series = request.args.get("series", default=None, type=str)
      program_code = request.args.get("code", default=None, type=str)
      cumulative = request.args.get("cumulative", default=True, type=bool)
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
      
      if cumulative:
        total = 0
        for d in data[::-1]:
          total += d["count"]
          d["count"] = total

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
        period = lower_bound.strftime("%m/%d")
      data.append({"period": period, 
      "series": s,
      "count": count})
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
        period = lower_bound.strftime("%m/%d")
      data.append({"period": period, 
      "series": s,
      "count": count})
    upper_bound = lower_bound
    lower_bound = upper_bound - relativedelta(weeks = 1)
    unit -= 1

  return data

def split_into_day(unit, today, data_since_old_date, series, include_year=True):
  data = []
  date = today
  while unit > 0:
    for s in series:
      if include_year:
        period = date.strftime("%m/%d/%Y")
      else:
        period = date.strftime("%m/%d")
      data.append({"period": period,
      "count": len([x for x in data_since_old_date if x['submitted'] == date and x['series'] == s])})
    date = date - relativedelta(days = 1)
    unit -= 1

  return data

def get_unit(start_date, end_date, period):
  unit = 0
  curr_date = start_date
  while curr_date < end_date:
    unit += 1

    if period == "month":
      curr_date = curr_date + relativedelta(months = 1)
    elif period == "week":
      curr_date = curr_date + relativedelta(weeks = 1)
    elif period == "day":
      curr_date = curr_date + relativedelta(days = 1)

  return unit

def valid_timeframe(start, end):
  return start >= "10/01" and end >= "10/01" and start <= end or start >= "10/01" and end <= "07/31" or start <= "07/31" and end <= "07/31" and start <= end

# for each "cycle", get all the data between start and end month for each period
@trends_api.route("/cycle", methods=["GET"])
class TrendsCycleApi(Resource):
    def get(self):
      query = base_query()

      period = request.args.get("period", default="month", type=str).lower()
      cycles = request.args.get("cycle", default=None, type=str) # e.g. cycle=21,22,23
      cumulative = request.args.get("cumulative", default=True, type=bool)
      start = request.args.get("start", default="10/01", type=str)
      end = request.args.get("end", default="07/31", type=str)
      series = request.args.get("series", default=None, type=str)
      program_code = request.args.get("code", default=None, type=str)
      gender = request.args.get("gender", default=None, type=str)
      fee_status = request.args.get("fee_status", default=None, type=str)
      nationality = request.args.get("nationality", default=None, type=str)

      if not valid_timeframe(start, end):
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
      for cycle in cycles:
        applicants = [applicant_deserializer.dump(d) for d in query.filter(Applicant.admissions_cycle == int(cycle))]
        if series:
          applicants = list(map(lambda x: {'submitted': datetime.strptime(x['submitted'], "%Y-%m-%d").date(), 'series': x[series]}, applicants))
        else:
          applicants = list(map(lambda x: {'submitted': datetime.strptime(x['submitted'], "%Y-%m-%d").date(), 'series': 'ALL'}, applicants))

        if start < "10/01":
          start_date = datetime.strptime(f"{cycle}/{start}", "%Y/%m/%d").date()
        else:
          start_date = datetime.strptime(f"{int(cycle) - 1}/{start}", "%Y/%m/%d").date()
        
        if end <= "07/31":
          end_date = datetime.strptime(f"{cycle}/{end}", "%Y/%m/%d").date()
        else:
          end_date = datetime.strptime(f"{int(cycle) - 1}/{end}", "%Y/%m/%d").date()
        
        unit = get_unit(start_date, end_date, period)

        if period == "month":
          today = start_date + relativedelta(months=unit)
        elif period == "week":
          today = start_date + relativedelta(weeks=unit)
        elif period == "day":
          today = start_date + relativedelta(days=unit)

        if period == "month":
          new_data = split_into_month(unit, today, applicants, series_types, upper_bound_inclusive=False)
        elif period == "week":
          new_data = split_into_week(unit, today, applicants, series_types, upper_bound_inclusive=False)
        elif period == "day":
          new_data = split_into_day(unit, today, applicants, series_types, include_year=False)
        
        if cumulative:
          total = 0
          for d in new_data[::-1]:
            total += d["count"]
            d["series"] = cycle
            d["count"] = total
        
        for d in new_data:
          d["series"] = cycle
          data.append(d)
      return data, 200
      