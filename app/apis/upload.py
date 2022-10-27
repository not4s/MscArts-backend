import os

from app import api
from app.database import db
from flask import request, abort
from flask_restx import Resource
import app.utils.parser as Parser
from app.apis.user import write_access_required


upload_api = api.namespace("api/upload", description="Test API")

ALLOWED_EXTENSIONS = {"xlsx", "csv"}


def validate_file(file):
    return True


@upload_api.route("/", methods=["POST"])
class UploadApi(Resource):
    @write_access_required
    def post(self):
        if "file" not in request.files:
            abort(406, description="No Files Found")

        file = request.files["file"]

        print("good")

        if file.filename == "":
            abort(406, description="no file found")

        if file and validate_file(file):
            df = Parser.csv_to_df(file, is_csv=file.filename.endswith(".csv"))
            Parser.insert_into_database(df)

        data = {"message": "file uploaded"}
        return data, 200
