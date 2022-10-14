import pandas as pd

from faker import Faker
from datetime import datetime
from app.database import db 
from app.models.applicant import Applicant, ApplicantStatus

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
    email = f'{f_name}.{l_name}@{fake.domain_name()}'
    b_date = fake.date_between_dates(date_start=datetime(1980,1,1), date_end=datetime(2005,12,31)).year
    
    new_df.loc[x, 'First Name'] = f_name
    new_df.loc[x, 'Last Name'] = l_name
    new_df.loc[x, 'Birth Date'] = str(b_date)
    new_df.loc[x, 'Email Address'] = email

  return new_df

# creates the applicant and applicantStatus objects for the given row
def create_applicant_and_status(df):
  #todo
  print(df)


# inserts values in the given dataframe to the database
def insert_into_database(df):
  new_data = []
  for x in df.index:
    print(df.iloc[x])
    print(type(df.iloc[x]))
    create_applicant_and_status(df.iloc[x])

    new_data.append(Applicant(erpid=int(df.loc[x, 'Erpid']), prefix=df.loc[x, 'Prefix'], first_name=df.loc[x, 'First Name'], 
    last_name=df.loc[x, 'Last Name'], gender=df.loc[x, 'Gender'],
    nationality=df.loc[x, 'Primary Nationality'], 
    email=df.loc[x, 'Email Address'], fee_status=df.loc[x, 'Fee Status'],
    program_code=df.loc[x, 'Programme Code']))

    new_data.append(ApplicantStatus(id=df.loc[x, 'Erpid'], status=df.loc[x, 'Application Status'], 
    supplemental_complete='yes' in df.loc[x, 'Supplemental Items Complete'].lower(), academic_eligibility=df.loc[x, 'Academic Eligibility'],
    folder_status=df.loc[x, 'Folder Status'], date_to_department=datetime.strptime(df.loc[x, 'Date Sent to Department'], '%d/%m/%y').date(), department_status=df.loc[x, 'Department Processing Status'], 
    special_case_status=df.loc[x, 'Special Case Status'], proposed_decision=df.loc[x, 'Proposed Decision'], 
    submitted=datetime.strptime(df.loc[x, 'Submitted Date'], '%d/%m/%y').date(), marked_complete=datetime.strptime(df.loc[x, 'Marked Complete Date'], '%d/%m/%y').date()))
  db.session.add_all(new_data)
  db.session.commit()

# Parses a file and inserts into database
def parse(filename):
  df = to_csv(filename)
  df_with_dummies = create_dummy_for_missing_fields(df) 
  insert_into_database(df_with_dummies)

def parse_by_gender(filename):
  parse(filename)
