import pandas as pd

from faker import Faker
from datetime import datetime
from app.database import db
from app.models.applicant import Applicant, ApplicantStatus, Program

# File extension check
def to_csv(file, is_csv):
    col_names = [
        "Anticipated Entry Term",
        "Erpid",
        "Prefix",
        "First Name",
        "Last Name",
        "Gender",
        "Birth Date",
        "Nationality",
        "Email",
        "Fee Status",
        "Type",
        "Academic College",
        "IC Department",
        "Programme Code",
        "Academic Program",
        "Academic Level",
        "Application Status",
        "Supplemental Items Complete",
        "Academic Eligibility",
        "Folder Status",
        "Date Sent to Department",
        "Department Processing Status",
        "Special Case Status",
        "Proposed Decision",
        "Submitted Date",
        "Marked Complete Date",
    ]

    if is_csv:
        return pd.read_csv(file, names=col_names, header=None, keep_default_na=False)
    else:
        return pd.read_excel(file, names=col_names, header=None, keep_default_na=False)


# Dummy for fields missing due to privacy concerns
def create_dummy_for_missing_fields(df):
    fake = Faker()
    Faker.seed(137920)
    new_df = df
    for x in new_df.index:
        f_name = fake.first_name()
        l_name = fake.last_name()
        email = f"{f_name}.{l_name}@{fake.domain_name()}"
        b_date = fake.date_between_dates(
            date_start=datetime(1980, 1, 1), date_end=datetime(2005, 12, 31)
        ).year

        new_df.loc[x, "First Name"] = f_name
        new_df.loc[x, "Last Name"] = l_name
        new_df.loc[x, "Birth Date"] = str(b_date)
        new_df.loc[x, "Email Address"] = email

    return new_df


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


# Parses a file and inserts into database
def parse(file, is_csv=False):
    df = to_csv(file, is_csv)
    df_with_dummies = create_dummy_for_missing_fields(df)
    insert_into_database(df_with_dummies)


def parse_by_gender(file):
    parse(file)
