from app import api
from app.database import db
from app.models.applicant import Applicant, Program
from app.schemas.applicant import ApplicantSchema, ProgramSchema
from app.utils.applicant import base_query, fetch_applicants
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
    cumulative = request.args.get("cumulative", default=1, type=int)
    gender = request.args.get("gender", default=None, type=str)
    fee_status = request.args.get("fee_status", default=None, type=str)
    nationality = request.args.get("nationality", default=None, type=str)

    program_type_filter = request.args.get("program_type", default=None, type=str)
    decision_status_filter = request.args.get(
      "decision_status", default=None, type=str
    )
    custom_decision = request.args.get("custom_decision", default=None, type=str)

    applicants = fetch_applicants(
      program_type_filter, decision_status_filter, custom_decision
    )

    if not series:
      if gender is not None:
        applicants = list(filter(lambda x: x['gender'] == gender, applicants))

      if nationality is not None:
        applicants = list(filter(lambda x: x['nationality'] == nationality, applicants))
      
      if fee_status is not None:
        applicants = list(filter(lambda x: x['fee_status'] == fee_status, applicants))
      
    if not unit:
      # return all years data
      return all_year_data(query, series, cumulative), 200

    today = date.today()

    if period == "year":
      old_date = today - relativedelta(years = unit)
    elif period == "month":
      old_date = today - relativedelta(months = unit)
    elif period == "week":
      old_date = today - relativedelta(weeks = unit)
    elif period == "day":
      old_date = today - relativedelta(days = unit)

    applicants = list(filter(lambda x: datetime.strptime(x['submitted'], "%Y-%m-%d").date() > old_date, applicants))
    if series:
      applicants = list(map(lambda x: {'submitted': datetime.strptime(x['submitted'], "%Y-%m-%d").date(), 'series': x[series]}, applicants))
      series = set([applicant_deserializer.dump(d)[series] for d in db.session.query(Applicant)])
    else:
      applicants = list(map(lambda x: {'submitted': datetime.strptime(x['submitted'], "%Y-%m-%d").date(), 'series': 'ALL'}, applicants))
      series = set(['ALL'])

    data = []
    if period == "year":
      data = split_into_year(unit, old_date, applicants, series, cumulative)
    elif period == "month":
      data = split_into_month(unit, old_date, applicants, series, cumulative)
    elif period == "week":
      data = split_into_week(unit, old_date, applicants, series, cumulative)
    elif period == "day":
      data = split_into_day(unit, old_date, applicants, series, cumulative)

    return data, 200

def all_year_data(applicants, series, cumulative):
  years_data = [applicant_deserializer.dump(d) for d in db.session.query(Applicant.admissions_cycle).distinct()]
  if cumulative == 1:
    series_total = dict.fromkeys(series, 0)
  if series is not None:
    series_data = set([applicant_deserializer.dump(d)[series] for d in db.session.query(Applicant)])
    applicants = list(map(lambda x: {'admissions_cycle': x['admissions_cycle'], series: x[series]}, applicants))
  else:
    series_data = ["ALL"]
    applicants = list(map(lambda x: {'admissions_cycle': x['admissions_cycle'], series: 'ALL'}, applicants))

  data = []
  for year_data in years_data:
    year = year_data["admissions_cycle"]

    for s in series_data:
      count = len([x for x in applicants if x['admissions_cycle'] == year and x['series'] == s])
      if cumulative == 1:
        series_total[s] += count
        count = series_total[s]
      
      data.append({"period": year, "series": s, "count": count})
  
  return data
  

def split_into_year(unit, today, data_since_old_date, series, cumulative):
  data = []
  lower_bound = today
  upper_bound = today + relativedelta(years = 1)

  if cumulative == 1:
    series_total = dict.fromkeys(series, 0)

  while unit > 0:
    for s in series:
      count = len([x for x in data_since_old_date if x['submitted'] > lower_bound and x['submitted'] <= upper_bound and x['series'] == s])
      if cumulative == 1:
        series_total[s] += count
        count = series_total[s]
      data.append({"period": (lower_bound + relativedelta(days = 1)).strftime("%m/%d/%Y"),
      "series": s,
      "count": count})
    lower_bound = upper_bound
    upper_bound = upper_bound + relativedelta(years = 1)
    unit -= 1
  return data

def split_into_month(unit, today, data_since_old_date, series, cumulative, upper_bound_inclusive=True):
  data = []
  lower_bound = today
  upper_bound = today + relativedelta(months = 1)

  if cumulative == 1:
    series_total = dict.fromkeys(series, 0)
  while unit > 0:
    for s in series:
      if (upper_bound_inclusive):
        count = len([x for x in data_since_old_date if x['submitted'] > lower_bound and x['submitted'] <= upper_bound and x['series'] == s])
        period = (lower_bound + relativedelta(days = 1)).strftime("%m/%d/%Y")
      else:
        count = len([x for x in data_since_old_date if x['submitted'] >= lower_bound and x['submitted'] < upper_bound and x['series'] == s])
        period = lower_bound.strftime("%m/%d")
      if cumulative == 1:
        series_total[s] += count
        count = series_total[s]
      data.append({"period": period, 
      "series": s,
      "count": count})
    lower_bound = upper_bound
    upper_bound = lower_bound + relativedelta(months = 1)
    unit -= 1

  return data

def split_into_week(unit, today, data_since_old_date, series, cumulative, upper_bound_inclusive=True):
  data = []
  lower_bound = today
  upper_bound = today + relativedelta(weeks = 1)

  if cumulative == 1:
    series_total = dict.fromkeys(series, 0)
  while unit > 0:
    for s in series:
      if upper_bound_inclusive:
        count = len([x for x in data_since_old_date if x['submitted'] > lower_bound and x['submitted'] <= upper_bound and x['series'] == s])
        period = (lower_bound + relativedelta(days = 1)).strftime("%m/%d/%Y")
      else:
        count = len([x for x in data_since_old_date if x['submitted'] >= lower_bound and x['submitted'] < upper_bound and x['series'] == s])
        period = lower_bound.strftime("%m/%d")

      if cumulative == 1:
        series_total[s] += count
        count = series_total[s]
      data.append({"period": period, 
      "series": s,
      "count": count})
    lower_bound = upper_bound
    upper_bound = lower_bound + relativedelta(weeks = 1)
    unit -= 1

  return data

def split_into_day(unit, today, data_since_old_date, series, cumulative, include_year=True):
  data = []
  date = today

  if cumulative == 1:
    series_total = dict.fromkeys(series, 0)
  while unit > 0:
    for s in series:
      if include_year:
        period = date.strftime("%m/%d/%Y")
      else:
        period = date.strftime("%m/%d")
      count = len([x for x in data_since_old_date if x['submitted'] == date and x['series'] == s])
      if cumulative == 1:
          series_total[s] += count
          count = series_total[s]
      data.append({"period": period,
      "count": count})
    date = date + relativedelta(days = 1)
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
    period = request.args.get("period", default="month", type=str).lower()
    cycles = request.args.get("cycle", default=None, type=str) # e.g. cycle=21,22,23
    cumulative = request.args.get("cumulative", default=1, type=int)
    start = request.args.get("start", default="10/01", type=str)
    end = request.args.get("end", default="07/31", type=str)
    series = request.args.get("series", default=None, type=str)
    gender = request.args.get("gender", default=None, type=str)
    fee_status = request.args.get("fee_status", default=None, type=str)
    nationality = request.args.get("nationality", default=None, type=str)

    program_type_filter = request.args.get("program_type", default=None, type=str)
    decision_status_filter = request.args.get(
      "decision_status", default=None, type=str
    )
    custom_decision = request.args.get("custom_decision", default=None, type=str)

    if not valid_timeframe(start, end):
      return {"message": "Invalid time frame given"}, 400
    
    cycles = cycles.split(",")
    cycles = ["20" + cycle for cycle in cycles]
    data = []

    if series:
      series_types = set([applicant_deserializer.dump(d)[series] for d in db.session.query(Applicant)])
    else:
      series_types = set(['ALL'])

    for cycle in cycles:
      applicants = fetch_applicants(
        program_type_filter, decision_status_filter, custom_decision, year=int(cycle)
      )
      if series:
        applicants = list(map(lambda x: {'submitted': datetime.strptime(x['submitted'], "%Y-%m-%d").date(), 'series': x[series]}, applicants))
      else:
        if gender is not None:
          applicants = list(filter(lambda x: x['gender'] == gender, applicants))
        
        if fee_status is not None:
          applicants = list(filter(lambda x: x['combined_fee_status'] == fee_status, applicants))
        
        if nationality is not None:
          applicants = list(filter(lambda x: x['nationality'] == nationality, applicants))

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
        new_data = split_into_month(unit, start_date, applicants, series_types, cumulative, upper_bound_inclusive=False)
      elif period == "week":
        new_data = split_into_week(unit, start_date, applicants, series_types, cumulative, upper_bound_inclusive=False)
      elif period == "day":
        new_data = split_into_day(unit, start_date, applicants, series_types, cumulative, include_year=False)
      
      if series is None:
        for d in new_data:
          d["series"] = cycle
      
      data += new_data
    return data, 200
      