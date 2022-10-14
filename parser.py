import pandas as pd

from faker import Faker
from datetime import datetime

# File extension check
def to_csv(filename):
  col_names = ['Anticipated Entry Term', 'Erpid', 'Prefix', \
               'First Name', 'Last Name', 'Gender', 'Birth Date', \
               'Nationality', 'Email', 'Fee Status', 'Type', \
               'Academic College', 'IC Department', 'Programme Code', \
               'Academic Program', 'Academic Level', 'Application Status', \
               'Supplemental Items Complete', 'Academic Eligibility', \
               'Folder Status', 'Date Sent to Department', \
               'Department Processing Status', 'Special Case Status', \
               'Proposed Decision', 'Submitted Date', 'Marked Complete Date']

  if filename.endswith('.csv'):
    return pd.read_csv(filename, names=col_names, header=None)
  elif filename.endswith('.xlsx') or filename.endswith('.xls'):
    return pd.read_excel(filename, names=col_names, header=None)
  else:
    raise ValueError('File is not of any of the supported formats: Expected .csv, .xlsx or .xls')

# Dummy for fields missing due to privacy concerns
def create_dummy_for_missing_fields(df):
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

# Setup dummies for parsers
def setup(filename):
  df = to_csv(filename)
  df_with_dummies = create_dummy_for_missing_fields(df) 

def parse_by_gender(filename):
  setup(filename)


