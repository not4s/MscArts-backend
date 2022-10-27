import os

from app import api
from app.database import db
from flask import request, abort
from flask_restx import Resource
import app.utils.parser as Parser
from app.apis.user import write_access_required, admin_required
from werkzeug.utils import secure_filename
from app.models.applicant import Applicant
from app.models.files import FileControl
from app.schemas.files import FileControlSchema


upload_api = api.namespace("api/upload", description="Test API")

ALLOWED_EXTENSIONS = {"xlsx", "csv"}

file_control_serializer = FileControlSchema()


def validate_file(file):
    return True


@upload_api.route("/", methods=["GET", "POST", "DELETE"])
class UploadApi(Resource):
    @write_access_required
    def get(self):
        files = FileControl.query.all()
        data = [file_control_serializer.dump(d) for d in files]
        return data, 200

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

    @admin_required
    def delete(self):
        if not request.is_json:
            abort(406, description="MIME type is required to be application/json.")

        file_version = request.json.get("version", None)

        if file_version is None:
            return {"message": "No file version provided"}, 400

        if type(file_version) is not int:
            return {"message": "File version is not of right type"}, 400

        file = FileControl.query.filter_by(version=file_version).first()

        if file is None:
            return {"message": "No file with version specified found"}, 400

        to_delete = Applicant.query.filter_by(version=file_version).delete()
        db.session.delete(file)
        db.session.commit()
        return {"message": "Rolled Back File"}, 200
