import pandas as pd

from faker import Faker
from datetime import datetime

def to_csv(filename):
  if filename.endswith('.csv'):
    return pd.read_csv(filename)
  elif filename.endswith('.xlsx') or filename.endswith('.xls'):
    return pd.read_excel(filename)
  else:
    raise ValueError('File is not of any of the supported formats: Expected .csv, .xlsx or .xls')

def insert_missing_info(df):
  fake = Faker()
  Faker.seed(137920)
  new_df = df 
  for x in new_df.index:
    f_name = fake.unique.first_name()
    l_name = fake.unique.last_name()
    email = f"{f_name}.{l_name}@{fake.domain_name()}"
    b_date = fake.date_between_dates(date_start=datetime(1980,1,1), date_end=datetime(2005,12,31)).year
    
    new_df.loc[x, "First Name (Prospect) (Person)"] = f_name
    new_df.loc[x, "Last Name (Prospect) (Person)"] = l_name
    new_df.loc[x, "Birth Date (Prospect) (Person)"] = str(b_date)
    new_df.loc[x, "Email Address (Prospect) (Person)"] = email

  return new_df


def parser(filename):
  df = to_csv(filename)

  new_df = insert_missing_info(df) 

