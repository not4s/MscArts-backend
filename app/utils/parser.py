import pandas as pd

from enum import Enum
from datetime import datetime
from app.database import db 
from app.models.applicant import Applicant, ApplicantStatus, Program


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

  try:
    if filename.endswith('.csv'):
      return pd.read_csv(filename, names=col_names, header=None)
    elif filename.endswith('.xlsx') or filename.endswith('.xls'):
      return pd.read_excel(filename, names=col_names, header=None)
  except ValueError:
    print('File is not of any of the supported formats: Expected .csv, .xlsx or .xls')

def convert_time(time_str):
    if type(time_str) is datetime:
        return time_str

    if time_str and type(time_str) is str:
        datetime.strptime(time_str, "%m/%d/%Y").date()
    else:
        return None

# inserts values in the given dataframe to the database
def insert_into_database(df):
    new_data = []
    new_program_code = []
    count = 0
    program_codes = db.session.query(Program.code).all()
    print(program_codes)
    for x in df.index:
        if count == 0:
            count += 1
            continue

        print(df.iloc[x])
        print(type(df.iloc[x]))

        program_code = df.loc[x, "Programme Code"]
        if (program_code,) not in program_codes:
            new_program_code.append(
                Program(
                    code=program_code,
                    name=df.loc[x, "Academic Program"],
                    application_type=df.loc[x, "Type"],
                )
            )
            program_codes.append(program_code)
            print(program_codes)

        new_data.append(
            Applicant(
                erpid=count,
                prefix=df.loc[x, "Prefix"],
                first_name=df.loc[x, "First Name"],
                last_name=df.loc[x, "Last Name"],
                gender=df.loc[x, "Gender"],
                nationality=df.loc[x, "Nationality"],
                email=df.loc[x, "Email Address"],
                fee_status=df.loc[x, "Fee Status"],
                program_code=program_code,
            )
        )

        new_data.append(
            ApplicantStatus(
                id=count,
                status=df.loc[x, "Application Status"],
                supplemental_complete="yes"
                in df.loc[x, "Supplemental Items Complete"].lower(),
                academic_eligibility=df.loc[x, "Academic Eligibility"],
                folder_status=df.loc[x, "Folder Status"],
                date_to_department=convert_time(df.loc[x, "Date Sent to Department"]),
                department_status=df.loc[x, "Department Processing Status"],
                special_case_status=df.loc[x, "Special Case Status"],
                proposed_decision=df.loc[x, "Proposed Decision"],
                submitted=convert_time(df.loc[x, "Submitted Date"]),
                marked_complete=convert_time(df.loc[x, "Marked Complete Date"]),
            )
        )

        count += 1

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

  def __init__(self, filename):
    Parser.df = to_csv(filename)

  def parse(self, ParserConst):
    '''Parse the dataset'''
    pass

  def update(self, filename):
    '''Update the dataset'''
    pass

class GenderParser(Parser):
    
    male_df = pd.DataFrame()
    female_df = pd.DataFrame()

    def __init__(self, filename):
      Parser.__init__(self, filename)
      GenderParser.male_df = self.df[self.df['Gender'] == 'Male']
      GenderParser.female_df = self.df[self.df['Gender'] == 'Female']

    def parse(self, gender):
      return GenderParser.male_df \
        if gender == 'Male' else GenderParser.female_df

class NationalityParser(Parser):

  def __init__(self, filename):
    Parser.__init__(self, filename)

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

  def __init__(self, filename):
    Parser.__init__(self, filename)
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

  def __init__(self, filename):
    Parser.__init__(self, filename)
    for academic_level in AcademicLevelParser.academic_level_list:
      AcademicLevelParser.parsed_data[academic_level] \
        = self.df[self.df['Academic Level'] == academic_level]

  def parse(self, academic_level):
    return AcademicLevelParser.parsed_data[academic_level]

class ApplicationStatusParser(Parser):

  application_status_list = ['Marked Complete', 'Withdrawn']
  parsed_data = {}

  def __init__(self, filename):
    Parser.__init__(self, filename)
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

  def __init__(self, filename):
    Parser.__init__(self, filename)
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

  def __init__(self, filename):
    Parser.__init__(self, filename)
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

  def __init__(self, filename):
    Parser.__init__(self, filename)
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

  def __init__(self, filename):
    Parser.__init__(self, filename)

  def parse(self, status):
    pass

# TODO
# No data available at the moment
class SpecialCaseStatusParser(Parser):

  def __init__(self, filename):
    Parser.__init__(self, filename)

  def parse(self, status):
    pass

class ProposedDecisionParser(Parser):

  decision_list = ['Withdrawn', 'Condition Pending', 'Rejected', 'Condition Firm', \
                   'Uncondition Firm', 'Offer Withdrawn', 'Condition Declined', \
                   'Uncondition Declined', 'Condition Rejected', 'Deferred', \
                   'No Decision', 'Waitlist']
  parsed_data = {}

  def __init__(self, filename):
    Parser.__init__(self, filename)
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
  


