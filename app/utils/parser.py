import pandas as pd

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

drop_columns = [
    "(Do Not Modify) Application Folder",
    "(Do Not Modify) Row Checksum",
    "(Do Not Modify) Modified On",
]

# erpid = 1


def csv_to_df(filename, is_csv):
    if is_csv:
        df = pd.read_csv(filename)
        return df.rename(columns=col_names_map)
    else:
        df = pd.read_excel(filename)
        return df.rename(columns=col_names_map)


def applicant_data(row, deposit):
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
        deposit_paid=deposit,
    )


def convert_time(time_str):
    if type(time_str) is datetime:
        return time_str

    if time_str and type(time_str) is str:
        return datetime.strptime(time_str, "%m/%d/%Y").date()
    elif type(time_str) is pd._libs.tslibs.timestamps.Timestamp:
        return time_str.to_pydatetime()


def insert_erpid(df):
    df["Erpid"] = range(1, df.shape[0] + 1)


def insert_admissions_cycle(df):
    df["Admissions Cycle"] = df["Anticipated Entry Term"].apply(
        lambda x: str(x).split()[1].split("-")[0]
    )
    # df["Admissions Cycle"] = pd.to_numeric(df["Admissions Cycle"])


def drop_empty_rows(df):
    df.drop(labels=(set(drop_columns) & set(df.columns)), axis=1, inplace=True)
    df.dropna(how="all", inplace=True)
    df.reset_index(drop=True, inplace=True)

# def new_erpid(df):
#     if erpid < len(df.index):
#         erpid = len(df.index)
#     erpid += 1
#     return erpid

def fill_null_values(df):
    fake = Faker()
    Faker.seed(137920)
    df["First Name"] = df.apply(
        lambda row: fake.first_name()
        if row["First Name"] == "" or row["First Name"] is None
        else row["First Name"],
        axis=1,
    )
    df["Last Name"] = df.apply(
        lambda row: fake.last_name()
        if row["Last Name"] == "" or row["Last Name"] is None
        else row["Last Name"],
        axis=1,
    )
    df["Email"] = df.apply(
        lambda row: f'{row["First Name"]}.{row["Last Name"]}@{fake.domain_name()}'
        if row["First Name"] == "" or row["Email"] is None
        else row["Email"],
        axis=1,
    )
    # df["Erpid"] = df.apply(
    #     lambda row: new_erpid(df) if row["Erpid"] == "" or row["Erpid"] is None else row["Erpid"],
    #     axis=1
    # )
    df["Admissions Cycle"] = df["Admissions Cycle"].fillna(-1)

    # print(df["Erpid"])


def add_columns(df, file_version):
    for col in col_names_map.values():
        if col == "Admissions Cycle" and col not in df.columns:
            # insert admissions cycle into the columns
            insert_admissions_cycle(df)
        df[col] = df[col] if col in df.columns else ""
    df["version"] = file_version


def missing_program_codes(df):
    new_program_code = []
    program_codes = list(map(lambda x: x.code, Program.query.all()))
    for name, _ in df:
        program_code = name[0]
        program_name = name[1]
        academic_level = name[2]
        if program_code and program_code not in program_codes:
            new_program_code.append(
                Program(
                    code=program_code,
                    name=program_name,
                    academic_level=academic_level,
                    active=False,
                )
            )
            program_codes.append(program_code)
    return new_program_code


def add_to_database(data):
    db.session.add_all(data)
    db.session.commit()


def format_rows(df, file_version):
    drop_empty_rows(df)
    add_columns(df, file_version)
    fill_null_values(df)
    insert_erpid(df)
    new_program_codes = missing_program_codes(
        df.groupby(["Programme Code", "Academic Program", "Type"])
    )
    add_to_database(new_program_codes)
    # print(pd.concat(g for _, g in df.groupby("Erpid") if len(g) > 1))


def get_new_applicants(applicants, deposit):
    new_applicants = []
    applicant_serializer = ApplicantSchema()
    database_data = [applicant_serializer.dump(d) for d in Applicant.query.all()]

    for d in database_data:
        del d["version"]

    for _, row in applicants.iterrows():
        new_applicant = applicant_data(row, deposit)
        json_new_applicant = applicant_serializer.dump(new_applicant)
        del json_new_applicant["version"]
        if json_new_applicant not in database_data:
            new_applicants.append(new_applicant)
    
    return new_applicants



# inserts values in the given dataframe to the database
def insert_into_database(df, file_version=0, deposit=False):
    format_rows(df, file_version)
    new_applicants = get_new_applicants(df, deposit)
    add_to_database(new_applicants)


def parse_to_models(df, deposit=False):
    df.dropna(how="all", inplace=True)
    df.reset_index(drop=True, inplace=True)

    # insert empty columns for all columns in our column name map that don't exist in the df
    for col in col_names_map.values():
        if col == "Admissions Cycle" and col not in df.columns:
            # insert admissions cycle into the columns
            insert_admissions_cycle(df)
        df[col] = df[col] if col in df.columns else ""
    df["First Name"] = df["First Name"].fillna("")
    df["Last Name"] = df["Last Name"].fillna("")
    df["Email"] = df["Email"].fillna("")
    df["Admissions Cycle"] = df["Admissions Cycle"].apply(lambda x: str(x)[:4])
    insert_erpid(df)

    fake = Faker()
    Faker.seed(137920)
    new_data = []
    applicant_serializer = ApplicantSchema()
    df = df.reindex(df.columns.tolist() + ["version"], axis=1)

    for _, row in df.iterrows():

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
        new_applicant = applicant_data(row, deposit)
        new_data.append(applicant_serializer.dump(new_applicant))
    return new_data
