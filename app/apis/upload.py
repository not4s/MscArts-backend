import os

from app import api
from app.database import db
from flask import request, abort
from flask_restx import Resource
import app.utils.parser as Parser
from app.apis.user import write_access_required
from werkzeug.utils import secure_filename
from app.models.files import FileControl
from app.schemas.files import FileControlSchema


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

        if file.filename == "":
            abort(406, description="No File found")

        if file and validate_file(file):
            new_file = FileControl(name=secure_filename(file.filename))
            db.session.add(new_file)
            db.session.commit()

            try:
                df = Parser.csv_to_df(file, is_csv=file.filename.endswith(".csv"))
                Parser.insert_into_database(df, new_file.version)
            except:
                db.session.delete(new_file)
                db.session.commit()
                return {"message": "Error when inserting data"}, 500

        return {"message": "File Successfully Uploaded"}, 200
