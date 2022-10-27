import pandas as pd

from enum import Enum
from datetime import datetime
from app.database import db 
from faker import Faker
from app.models.applicant import Applicant, Program

col_names = ['Version', 'Anticipated Entry Term', 'Erpid', 'Prefix', \
              'First Name', 'Last Name', 'Gender', 'Birth Date', \
              'Nationality', 'Email', 'Fee Status', 'Type', \
              'Academic College', 'IC Department', 'Programme Code', \
              'Academic Program', 'Academic Level', 'Application Status', \
              'Supplemental Items Complete', 'Academic Eligibility', \
              'Folder Status', 'Date Sent to Department', \
              'Department Processing Status', 'Special Case Status', \
              'Proposed Decision', 'Submitted Date', 'Marked Complete Date']


# File extension check
def csv_to_df(filename, is_csv):

  if (is_csv):
    return pd.read_csv(filename, names=col_names, header=None)
  else:
    return pd.read_excel(filename, names=col_names, header=None, keep_default_na=False)

def generate_df_from_sql(query):
  pass

def generate_df_from_db():
  program_data = db.session.query(Program).all()
  applicant_data = db.session.query(Applicant).all()
  applicant_status_data = db.session.query(ApplicantStatus).all()

  program_columns = ['Programme Code',
                     'Academic Program',
                     'Type']

  applicant_columns = ['Version',
                       'Anticipated Entry Term',
                       'Erpid',
                       'Prefix',
                       'First Name',
                       'Last Name',
                       'Gender',
                       'Nationality',
                       'Email',
                       'Fee Status']

  applicant_status_columns = ['Application Status',
                              'Supplemental Items Complete',
                              'Academic Eligibility',
                              'Folder Status',
                              'Date Sent to Department',
                              'Department Processing Status',
                              'Special Case Status',
                              'Proposed Decision',
                              'Submitted Date',
                              'Marked Complete Date']

  program_df \
    = pd.read_sql(sql = db.session.query(Program) \
                         .with_entities(Program.code,
                                        Program.name,
                                        Program.application_type).statement, 
                  con = db.session.bind, columns=program_columns)
  applicant_df \
    = pd.read_sql(sql = db.session.query(Applicant) \
                         .with_entities(Applicant.version,
                                        Applicant.anticipated_entry_term,
                                        Applicant.erpid,
                                        Applicant.prefix,
                                        Applicant.first_name,
                                        Applicant.last_name,
                                        Applicant.gender,
                                        Applicant.nationality,
                                        Applicant.email,
                                        Applicant.fee_status,
                                        Applicant.program_code).statement, 
                  con = db.session.bind, columns=applicant_columns)
  applicant_status_df \
    = pd.read_sql(sql = db.session.query(ApplicantStatus) \
                         .with_entities(ApplicantStatus.status,
                                        ApplicantStatus.supplemental_complete,
                                        ApplicantStatus.academic_eligibility,
                                        ApplicantStatus.folder_status,
                                        ApplicantStatus.date_to_department,
                                        ApplicantStatus.department_status,
                                        ApplicantStatus.special_case_status,
                                        ApplicantStatus.proposed_decision,
                                        ApplicantStatus.submitted,
                                        ApplicantStatus.marked_complete).statement, 
                  con = db.session.bind, columns=applicant_status_columns)

  output_df = pd.concat([program_df, applicant_df, applicant_status_df], axis=1)
  output_col_names = col_names[:]
  output_col_names.remove('Birth Date')
  output_col_names.remove('Academic College')
  output_col_names.remove('IC Department')
  output_col_names.remove('Academic Level')

  return output_df[col_names]



def convert_time(time_str):
    if type(time_str) is datetime:
        return time_str

    if time_str and type(time_str) is str:
        datetime.strptime(time_str, "%m/%d/%Y").date()
    else:
        return None

def insert_erpid(df):
  df['Erpid'] = range(1, df.shape[0] + 1)


# inserts values in the given dataframe to the database
def insert_into_database(df):

    df.dropna(how='all', inplace=True)
    df.reset_index(drop=True, inplace=True)
    df["First Name"] = df["First Name"].fillna('')
    df["Last Name"] = df["Last Name"].fillna('')
    df["Email"] = df["Email"].fillna('')
    insert_erpid(df)
    
    fake = Faker()
    Faker.seed(137920)
    new_data = []
    new_program_code = []

    program_codes = list(map(lambda x: x.code, Program.query.all()))
    database_df = Parser.df

    for index, row in df.iterrows():
        if index == 0:
          continue

        if df.iloc[index] in database_df:
          continue

        f_name = row["First Name"] if row["First Name"] != "" else fake.first_name()
        l_name = row["Last Name"] if row["Last Name"] != "" else fake.last_name()
        email = row["Email"] if row["Email"] != "" else f'{f_name}.{l_name}@{fake.domain_name()}'
        # b_date = fake.date_between_dates(date_start=datetime(1980,1,1), date_end=datetime(2005,12,31)).year

        program_code = row["Programme Code"]
        if program_code not in program_codes:
            new_program_code.append(
                Program(
                    code=program_code,
                    name=row["Academic Program"],
                    application_type=row["Type"],
                )
            )
            program_codes.append(program_code)

        # Fetch the latest version saved in db of the given erpid
        version_parser = VersionParser()
        version = version_parser.getLatestVersion(row["Erpid"])

        if not version: # If no prior version is in db
          version = 1
        else:
          version += 1

        new_data.append(
            Applicant(
                version,
                anticipated_entry_term=row["Anticipated Entry Term"],
                erpid=row["Erpid"],
                prefix=row["Prefix"],
                first_name=f_name,
                last_name=l_name,
                gender=row["Gender"],
                nationality=row["Nationality"],
                email=email,
                fee_status=row["Fee Status"],
                program_code=program_code,
            )
        )

        new_data.append(
            ApplicantStatus(
                id=row["Erpid"],
                status=row["Application Status"],
                supplemental_complete="Yes" == row["Supplemental Items Complete"],
                academic_eligibility=row["Academic Eligibility"],
                folder_status=row["Folder Status"],
                date_to_department=convert_time(row["Date Sent to Department"]),
                department_status=row["Department Processing Status"],
                special_case_status=row["Special Case Status"],
                proposed_decision=row["Proposed Decision"],
                submitted=convert_time(row["Submitted Date"]),
                marked_complete=convert_time(row["Marked Complete Date"]),
            )
        )

    db.session.add_all(new_program_code)
    db.session.commit()
    db.session.add_all(new_data)
    db.session.commit()


'''
  Parser

  - Use Cases:
      Gender
      Nationality
      Programme Code = Academic Program
      Academic Level
      Application Status
      Supplemental Items Complete
      Academic Eligibility
      Folder Status
      Department Processing Status
      Proposed Decision 

    Every parser inherits the Parser interface which has two methods:
      parse and update

    The Parsed dataframes are stored as a class member to avoid redundant parsing.
'''
class Parser:

  def __init__(self):
    
    self.df = generate_df_from_db()

  def parse(self, context):
    '''Parse the dataset'''
    pass

  def update(self):
    '''Update the dataset'''
    pass

class VersionParser(Parser):
  
  version_map = {}
  parsed_data = {}

  def __init__(self):
    Parser.__init__(self)
    for erpid in self.df['Erpid']:
      if erpid not in VersionParser.version_map:
        VersionParser.version_map[erpid] = 1
      else:
        VersionParser.version_map[erpid] \
          = self.df[self.df["Erpid"] == erpid]["Version"]
    self.latest_version = max(self.version_list)

  def getLatestVersion(self, erpid):
    return self.version_map[erpid]

  def parse(self, version):
    pass

  
class AnticipatedEntryTermParser(Parser):

  term_list = []
  parsed_data = {}

  def __init__(self):
    Parser.__init__(self)
    for term in self.df['Anticipated Entry Term']:
      if term not in AnticipatedEntryTermParser.term_list:
        AnticipatedEntryTermParser.term_list.append(term)
      AnticipatedEntryTermParser.parsed_data[term] \
        = self.df[self.df['Anticipated Entry Term'] == term]
      

  def parse(self, year):
    try:
      if year in AnticipatedEntryTermParser.parsed_data:
        return AnticipatedEntryTermParser.parsed_data[year]
    except:
      print(f'No applicants for year {year}!')


class GenderParser(Parser):
    
  male_df = pd.DataFrame()
  female_df = pd.DataFrame()

  def __init__(self):
    Parser.__init__(self)
    GenderParser.male_df = self.df[self.df['Gender'] == 'Male']
    GenderParser.female_df = self.df[self.df['Gender'] == 'Female']

  def parse(self, gender):
    return GenderParser.male_df \
      if gender == 'Male' else GenderParser.female_df

class NationalityParser(Parser):

  def __init__(self):
    Parser.__init__(self)

  def parse(self, country):
    return self.df[self.df['Nationality'] == country]

class ProgramCodeParser(Parser):
  
  program_code_map = {'G5ZP.1'  : 'Computing Research(PhD)', \
                      'G5ZA.1'  : 'AI and Machine Learning(PhD 4YFT)', \
                      'G5ZB.1'  : 'AI and Machine Learning(MRes 1YFT)', \
                      'G5UO.1'  : 'Advanced Computing(MSc 1YFT)', \
                      'G5UX.1'  : 'Computing Taught Programmes(Occasional FT)', \
                      'G5ZS.1'  : 'Safe and Trusted Artificial Intelligence(PhD)', \
                      'G5U10.1' : 'Computing(Artificial Intelligence and Machine Learning)(MSc 1YFT)', \
                      'G5U6.1'  : 'Computing Science(MSc 1YFT)', \
                      'G5T1.1'  : 'Artificial Intelligence(MSc 1YFT)', \
                      'G5U16.1' : 'Computing(Software Engineering)(MSc 1YFT)', \
                      'G5U6.2'  : 'Computing(MSc 1YFT)', \
                      'G5U13.2' : 'G5U13.2 = Computing(Visual Computing and Robotics)(MSc 1YFT)', \
                      'G5U11.3' : 'Computing(Management and Finance)(MSc 1YFT)', \
                      'G5U21.2' : 'Computing(Security and Reliability)', \
                      'G5ZD.1'  : 'Doctoral Teaching Programme in Computing(PhD)'}
  parsed_data= {}

  def __init__(self):
    Parser.__init__(self)
    for program_code in ProgramCodeParser.program_code_map:
      ProgramCodeParser.parsed_data[program_code] \
        = self.df[self.df['Programme Code'] == program_code]

  def parse(self, code):
    if code not in ProgramCodeParser.parsed_data:
      for program_code, academic_program in ProgramCodeParser.items():
        if code == academic_program:
          code = program_code
    return ProgramCodeParser.parsed_data[code]

class AcademicLevelParser(Parser):

  academic_level_list = ['PG Research', 'PG Research Masters', \
                         'PG Taught Degree', 'PG Taught Occasional']
  parsed_data = {}

  def __init__(self):
    Parser.__init__(self)
    for academic_level in AcademicLevelParser.academic_level_list:
      AcademicLevelParser.parsed_data[academic_level] \
        = self.df[self.df['Academic Level'] == academic_level]

  def parse(self, academic_level):
    return AcademicLevelParser.parsed_data[academic_level]

class ApplicationStatusParser(Parser):

  application_status_list = ['Marked Complete', 'Withdrawn']
  parsed_data = {}

  def __init__(self):
    Parser.__init__(self)
    ApplicationStatusParser.parsed_data['NaN'] \
      = self.df[self.df['Application Status'].isna()]
    for application_status in ApplicationStatusParser.application_status_list:
      ApplicationStatusParser.parsed_data[application_status] \
        = self.df[self.df['Application Status'] == application_status]

  def parse(self, application_status):
    return ApplicationStatusParser.parsed_data[application_status]

class SupplementalItemsCompleteStatusParser(Parser):

  completed = pd.DataFrame()
  not_completed = pd.DataFrame()

  def __init__(self):
    Parser.__init__(self)
    SupplementalItemsCompleteStatusParser.completed \
      = self.df[self.df['Supplemental Items Complete'] == 'Yes']
    SupplementalItemsCompleteStatusParser.not_completed \
      = self.df[self.df['Supplemental Items Complete'].isna()]

  def parse(self, complete_status):
    return SupplementalItemsCompleteStatusParser.completed \
      if complete_status == 'Yes' \
      else SupplementalItemsCompleteStatusParser.not_completed

class AcademicEligibilityParser(Parser):

  eligibility_list = ['Proceed - Meets Department Requirements', \
                      'Proceed - Pending Results', \
                      'Reject at Source', \
                      'Department Review - Below College Requirements', \
                      'Proceed - Below Department Requirements/Above College Minimum', \
                      'Exempt from Admission Requirements']
  parsed_data = {}

  def __init__(self):
    Parser.__init__(self)
    AcademicEligibilityParser.parsed_data['NaN'] \
      = self.df[self.df['Academic Eligibility'].isna()]
    for eligibility in AcademicEligibilityParser.eligibility_list:
      AcademicEligibilityParser.parsed_data[eligibility] \
        = self.df[self.df['Academic Eligibility'] == eligibility]

  def parse(self, eligibility):
    return AcademicEligibilityParser.parsed_data[eligibility]

class FolderStatusParser(Parser):
  folder_status_list = ['Admissions - Ready for Review', \
                        'Admissions - Review Cancelled', \
                        'Department - Ready for Review', \
                        'Admissions - Decision Made', \
                        'Reconsideration', \
                        'Admissions - Offer Deferred', \
                        'Admissions - Deferral to process', \
                        'Admissions - Review Pending more Information', \
                        'Admissions - Review on Hold', \
                        'Department - Waiting List']
  parsed_data = {}

  def __init__(self):
    Parser.__init__(self)
    FolderStatusParser.parsed_data['NaN'] \
      = self.df[self.df['Folder Status'].isna()]
    for folder_status in FolderStatusParser.folder_status_list:
      FolderStatusParser.parsed_data[folder_status] \
        = self.df[self.df['Folder Status'] == folder_status]

  def parse(self, folder_status):
    return FolderStatusParser.parsed_data[folder_status]

# TODO
# No data available at the moment    
class DepartmentProcessingStatusParser(Parser):

  def __init__(self):
    Parser.__init__(self)

  def parse(self, status):
    pass

# TODO
# No data available at the moment
class SpecialCaseStatusParser(Parser):

  def __init__(self):
    Parser.__init__(self)

  def parse(self, status):
    pass

class ProposedDecisionParser(Parser):

  decision_list = ['Withdrawn', 'Condition Pending', 'Rejected', 'Condition Firm', \
                   'Uncondition Firm', 'Offer Withdrawn', 'Condition Declined', \
                   'Uncondition Declined', 'Condition Rejected', 'Deferred', \
                   'No Decision', 'Waitlist']
  parsed_data = {}

  def __init__(self):
    Parser.__init__(self)
    ProposedDecisionParser.parsed_data['NaN'] \
      = self.df[self.df['Proposed Decision'].isna()]
    for decision in ProposedDecisionParser.decision_list:
      ProposedDecisionParser.parsed_data[decision] \
        = self.df[self.df['Proposed Decision'] == decision]

  def parse(self, decision):
    return ProposedDecisionParser.parsed_data[decision]

# FOR SIMPLE TESTING USAGE
def main():
  gp = GenderParser('./application_data.xlsx')
  gp.parse('Female')
  with open('output.txt', 'w') as f:
    f.write(GenderParser.female_df.to_string())

if __name__ == '__main__':
  main()
  


