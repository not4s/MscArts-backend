import pandas as pd

from enum import Enum
from datetime import datetime
from app.database import db
from faker import Faker
from app.models.applicant import Applicant, Program
from app.schemas.applicant import ApplicantSchema

col_names_map = {
    "erpid (Prospect) (Person)": "Erpid",
    "Prospect Gender (Prospect) (Person)": "Gender",
    "Prefix (Prospect) (Person)": "Prefix",
    "First Name (Prospect) (Person)": "First Name",
    "Last Name (Prospect) (Person)": "Last Name",
    "Birth Date (Prospect) (Person)": "Birth Date",
    "IC Ethnicity (Prospect) (Person)": "Ethnicity",
    "Email Address (Prospect) (Person)": "Email",
    "Application Type": "Type",
    "Academic College (Academic Program) (Academic Programme)": "Academic College",
    "IC Department (Academic Program) (Academic Programme)": "IC Department",
    "Disability Type (Application) (Application)": "Disability Type",
    "Primary Nationality (Prospect) (Person)": "Primary Nationality",
    "Country of Residency (Application) (Application)": "Country of Residency",
    "Application Folder Fee Status": "Application Folder Fee Status",
    "Combined Fee Status": "Combined Fee Status",
    "Admissions Cycle (Opportunity) (Opportunity)": "Admissions Cycle",
    "Anticipated Entry Term (Application) (Application)": "Anticipated Entry Term",
    "Academic Program (Application) (Application)": "Academic Program",
    "Programme Code (Academic Program) (Academic Programme)": "Programme Code",
    "Academic Level (Application) (Application)": "Academic Level",
    "Application Status (Application) (Application)": "Application Status",
    "Supplemental Items Complete (Application) (Application)": "Supplemental Items Complete",
    "Department Processing Status": "Department Processing Status",
    "Special Case Status": "Special Case Status",
    "Folder Status": "Folder Status",
    "Academic Eligibility": "Academic Eligibility",
    "Proposed Decision": "Proposed Decision",
    "Decision Status": "Decision Status",
    "Status (Opportunity) (Opportunity)": "Status",
    "Status Reason (Opportunity) (Opportunity)": "Status Reason",
    "Submitted (Opportunity) (Opportunity)": "Submitted Date",
    "Withdrawn (Opportunity) (Opportunity)": "Withdrawn Date",
    "Marked Complete (Opportunity) (Opportunity)": "Marked Complete Date",
    "Date Sent to Department": "Date Sent to Department",
    "Admitted (Opportunity) (Opportunity)": "Admitted Date",
    "Deferred (Opportunity) (Opportunity)": "Deferred Date",
    "Enrolled (Opportunity) (Opportunity)": "Enrolled Date",
}

# File extension check
def csv_to_df(filename, is_csv):
    if is_csv:
        df = pd.read_csv(filename)
        return df.rename(columns=col_names_map)
    else:
        df = pd.read_excel(filename, keep_default_na=False)
        return df.rename(columns=col_names_map)


def applicant_data(row):
    return Applicant(
        version=row["version"],
        anticipated_entry_term=row["Anticipated Entry Term"],
        admissions_cycle=row["Admissions Cycle"],
        erpid=row["Erpid"],
        prefix=row["Prefix"],
        first_name=row["First Name"],
        last_name=row["Last Name"],
        gender=row["Gender"],
        birth_date=convert_time(row["Birth Date"]),
        nationality=row["Primary Nationality"],
        ethnicity=row["Ethnicity"],
        disability=row["Disability Type"],
        country_of_residency=row["Country of Residency"],
        email=row["Email"],
        application_folder_fee_status=row["Application Folder Fee Status"],
        combined_fee_status=row["Combined Fee Status"],
        program_code=row["Programme Code"],
        application_status=row["Application Status"],
        supplemental_complete="Yes" == row["Supplemental Items Complete"],
        academic_eligibility=row["Academic Eligibility"],
        folder_status=row["Folder Status"],
        date_to_department=convert_time(row["Date Sent to Department"]),
        department_status=row["Department Processing Status"],
        special_case_status=row["Special Case Status"],
        proposed_decision=row["Proposed Decision"],
        decision_status=row["Decision Status"],
        status=row["Status"],
        status_reason=row["Status Reason"],
        submitted=convert_time(row["Submitted Date"]),
        withdrawn=convert_time(row["Withdrawn Date"]),
        admitted=convert_time(row["Admitted Date"]),
        deferred=convert_time(row["Deferred Date"]),
        enrolled=convert_time(row["Enrolled Date"]),
        marked_complete=convert_time(row["Marked Complete Date"]),
    )


def generate_df_from_sql(query):
    pass


def generate_df_from_db():
    pass


def convert_time(time_str):
    if type(time_str) is datetime:
        return time_str

    if time_str and type(time_str) is str:
        datetime.strptime(time_str, "%m/%d/%Y").date()
    else:
        return None


def insert_erpid(df):
    df["Erpid"] = range(1, df.shape[0] + 1)


def parse_to_models(df):
    df.dropna(how="all", inplace=True)
    df.reset_index(drop=True, inplace=True)

    # insert empty columns for all columns in our column name map that don't exist in the df
    for col in col_names_map.values():
        df[col] = df[col] if col in df.columns else ""
    df["First Name"] = df["First Name"].fillna("")
    df["Last Name"] = df["Last Name"].fillna("")
    df["Email"] = df["Email"].fillna("")
    insert_erpid(df)

    fake = Faker()
    Faker.seed(137920)
    new_data = []
    new_program_code = []
    applicant_serializer = ApplicantSchema()
    df = df.reindex(df.columns.tolist() + ["version"], axis=1)

    for index, row in df.iterrows():

        row["First Name"] = (
            row["First Name"] if row["First Name"] else fake.first_name()
        )
        row["Last Name"] = row["Last Name"] if row["Last Name"] else fake.last_name()
        row["Email"] = (
            row["Email"]
            if row["Email"]
            else f'{row["First Name"]}.{row["Last Name"]}@{fake.domain_name()}'
        )
        row["version"] = -1
        new_applicant = applicant_data(row)
        new_data.append(applicant_serializer.dump(new_applicant))
    return new_data


# inserts values in the given dataframe to the database
def insert_into_database(df, file_version=0, mock=False):
    df.dropna(how="all", inplace=True)
    df.reset_index(drop=True, inplace=True)

    # insert empty columns for all columns in our column name map that don't exist in the df
    for col in col_names_map.values():
        df[col] = df[col] if col in df.columns else ""
    df["First Name"] = df["First Name"].fillna("")
    df["Last Name"] = df["Last Name"].fillna("")
    df["Email"] = df["Email"].fillna("")

    fake = Faker()
    Faker.seed(137920)
    new_data = []
    new_program_code = []

    program_codes = list(map(lambda x: x.code, Program.query.all()))
    # database_df = generate_df_from_db()
    applicant_serializer = ApplicantSchema()
    database_data = [applicant_serializer.dump(d) for d in Applicant.query.all()]

    for d in database_data:
        del d["version"]

    df = df.reindex(df.columns.tolist() + ["version"], axis=1)

    erpid = 1

    for index, row in df.iterrows():

        row["First Name"] = (
            row["First Name"] if row["First Name"] else fake.first_name()
        )
        row["Last Name"] = row["Last Name"] if row["Last Name"] else fake.last_name()
        row["Email"] = (
            row["Email"]
            if row["Email"]
            else f'{row["First Name"]}.{row["Last Name"]}@{fake.domain_name()}'
        )
        if not row["Erpid"]:
            row["Erpid"] = erpid
            erpid += 1
        # b_date = fake.date_between_dates(date_start=datetime(1980,1,1), date_end=datetime(2005,12,31)).year

        program_code = row["Programme Code"]
        if program_code not in program_codes:
            new_program_code.append(
                Program(
                    code=program_code,
                    name=row["Academic Program"],
                    academic_level=row["Type"],
                    active=False,
                )
            )
            program_codes.append(program_code)

        # Fetch the latest version saved in db of the given erpid
        # version_parser = VersionParser()
        row["version"] = file_version

        new_applicant = applicant_data(row)
        json_new_applicant = applicant_serializer.dump(new_applicant)
        del json_new_applicant["version"]
        if json_new_applicant not in database_data:
            new_data.append(new_applicant)

    db.session.add_all(new_program_code)
    db.session.commit()
    db.session.add_all(new_data)
    db.session.commit()


"""
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
"""


class Parser:
    def __init__(self):

        self.df = generate_df_from_db()

    def parse(self, context):
        """Parse the dataset"""
        pass

    def update(self):
        """Update the dataset"""
        pass


class VersionParser(Parser):

    version_map = {}
    parsed_data = {}

    def __init__(self):
        Parser.__init__(self)
        for erpid in self.df["Erpid"]:
            if erpid not in VersionParser.version_map:
                VersionParser.version_map[erpid] = 1
            else:
                VersionParser.version_map[erpid] = self.df[self.df["Erpid"] == erpid][
                    "Version"
                ]
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
        for term in self.df["Anticipated Entry Term"]:
            if term not in AnticipatedEntryTermParser.term_list:
                AnticipatedEntryTermParser.term_list.append(term)
            AnticipatedEntryTermParser.parsed_data[term] = self.df[
                self.df["Anticipated Entry Term"] == term
            ]

    def parse(self, year):
        try:
            if year in AnticipatedEntryTermParser.parsed_data:
                return AnticipatedEntryTermParser.parsed_data[year]
        except:
            print(f"No applicants for year {year}!")


class GenderParser(Parser):

    male_df = pd.DataFrame()
    female_df = pd.DataFrame()

    def __init__(self):
        Parser.__init__(self)
        GenderParser.male_df = self.df[self.df["Gender"] == "Male"]
        GenderParser.female_df = self.df[self.df["Gender"] == "Female"]

    def parse(self, gender):
        return GenderParser.male_df if gender == "Male" else GenderParser.female_df


class NationalityParser(Parser):
    def __init__(self):
        Parser.__init__(self)

    def parse(self, country):
        return self.df[self.df["Nationality"] == country]


class ProgramCodeParser(Parser):

    program_code_map = {
        "G5ZP.1": "Computing Research(PhD)",
        "G5ZA.1": "AI and Machine Learning(PhD 4YFT)",
        "G5ZB.1": "AI and Machine Learning(MRes 1YFT)",
        "G5UO.1": "Advanced Computing(MSc 1YFT)",
        "G5UX.1": "Computing Taught Programmes(Occasional FT)",
        "G5ZS.1": "Safe and Trusted Artificial Intelligence(PhD)",
        "G5U10.1": "Computing(Artificial Intelligence and Machine Learning)(MSc 1YFT)",
        "G5U6.1": "Computing Science(MSc 1YFT)",
        "G5T1.1": "Artificial Intelligence(MSc 1YFT)",
        "G5U16.1": "Computing(Software Engineering)(MSc 1YFT)",
        "G5U6.2": "Computing(MSc 1YFT)",
        "G5U13.2": "G5U13.2 = Computing(Visual Computing and Robotics)(MSc 1YFT)",
        "G5U11.3": "Computing(Management and Finance)(MSc 1YFT)",
        "G5U21.2": "Computing(Security and Reliability)",
        "G5ZD.1": "Doctoral Teaching Programme in Computing(PhD)",
    }
    parsed_data = {}

    def __init__(self):
        Parser.__init__(self)
        for program_code in ProgramCodeParser.program_code_map:
            ProgramCodeParser.parsed_data[program_code] = self.df[
                self.df["Programme Code"] == program_code
            ]

    def parse(self, code):
        if code not in ProgramCodeParser.parsed_data:
            for program_code, academic_program in ProgramCodeParser.items():
                if code == academic_program:
                    code = program_code
        return ProgramCodeParser.parsed_data[code]


class AcademicLevelParser(Parser):

    academic_level_list = [
        "PG Research",
        "PG Research Masters",
        "PG Taught Degree",
        "PG Taught Occasional",
    ]
    parsed_data = {}

    def __init__(self):
        Parser.__init__(self)
        for academic_level in AcademicLevelParser.academic_level_list:
            AcademicLevelParser.parsed_data[academic_level] = self.df[
                self.df["Academic Level"] == academic_level
            ]

    def parse(self, academic_level):
        return AcademicLevelParser.parsed_data[academic_level]


class ApplicationStatusParser(Parser):

    application_status_list = ["Marked Complete", "Withdrawn"]
    parsed_data = {}

    def __init__(self):
        Parser.__init__(self)
        ApplicationStatusParser.parsed_data["NaN"] = self.df[
            self.df["Application Status"].isna()
        ]
        for application_status in ApplicationStatusParser.application_status_list:
            ApplicationStatusParser.parsed_data[application_status] = self.df[
                self.df["Application Status"] == application_status
            ]

    def parse(self, application_status):
        return ApplicationStatusParser.parsed_data[application_status]


class SupplementalItemsCompleteStatusParser(Parser):

    completed = pd.DataFrame()
    not_completed = pd.DataFrame()

    def __init__(self):
        Parser.__init__(self)
        SupplementalItemsCompleteStatusParser.completed = self.df[
            self.df["Supplemental Items Complete"] == "Yes"
        ]
        SupplementalItemsCompleteStatusParser.not_completed = self.df[
            self.df["Supplemental Items Complete"].isna()
        ]

    def parse(self, complete_status):
        return (
            SupplementalItemsCompleteStatusParser.completed
            if complete_status == "Yes"
            else SupplementalItemsCompleteStatusParser.not_completed
        )


class AcademicEligibilityParser(Parser):

    eligibility_list = [
        "Proceed - Meets Department Requirements",
        "Proceed - Pending Results",
        "Reject at Source",
        "Department Review - Below College Requirements",
        "Proceed - Below Department Requirements/Above College Minimum",
        "Exempt from Admission Requirements",
    ]
    parsed_data = {}

    def __init__(self):
        Parser.__init__(self)
        AcademicEligibilityParser.parsed_data["NaN"] = self.df[
            self.df["Academic Eligibility"].isna()
        ]
        for eligibility in AcademicEligibilityParser.eligibility_list:
            AcademicEligibilityParser.parsed_data[eligibility] = self.df[
                self.df["Academic Eligibility"] == eligibility
            ]

    def parse(self, eligibility):
        return AcademicEligibilityParser.parsed_data[eligibility]


class FolderStatusParser(Parser):
    folder_status_list = [
        "Admissions - Ready for Review",
        "Admissions - Review Cancelled",
        "Department - Ready for Review",
        "Admissions - Decision Made",
        "Reconsideration",
        "Admissions - Offer Deferred",
        "Admissions - Deferral to process",
        "Admissions - Review Pending more Information",
        "Admissions - Review on Hold",
        "Department - Waiting List",
    ]
    parsed_data = {}

    def __init__(self):
        Parser.__init__(self)
        FolderStatusParser.parsed_data["NaN"] = self.df[self.df["Folder Status"].isna()]
        for folder_status in FolderStatusParser.folder_status_list:
            FolderStatusParser.parsed_data[folder_status] = self.df[
                self.df["Folder Status"] == folder_status
            ]

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

    decision_list = [
        "Withdrawn",
        "Condition Pending",
        "Rejected",
        "Condition Firm",
        "Uncondition Firm",
        "Offer Withdrawn",
        "Condition Declined",
        "Uncondition Declined",
        "Condition Rejected",
        "Deferred",
        "No Decision",
        "Waitlist",
    ]
    parsed_data = {}

    def __init__(self):
        Parser.__init__(self)
        ProposedDecisionParser.parsed_data["NaN"] = self.df[
            self.df["Proposed Decision"].isna()
        ]
        for decision in ProposedDecisionParser.decision_list:
            ProposedDecisionParser.parsed_data[decision] = self.df[
                self.df["Proposed Decision"] == decision
            ]

    def parse(self, decision):
        return ProposedDecisionParser.parsed_data[decision]


# FOR SIMPLE TESTING USAGE
# def main():
#   gp = GenderParser('./application_data.xlsx')
#   gp.parse('Female')
#   with open('output.txt', 'w') as f:
#     f.write(GenderParser.female_df.to_string())

# if __name__ == '__main__':
#   main()
