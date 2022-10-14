import os

from app import api
from app.database import db 
from flask import request, abort
from flask_restx import Resource

from werkzeug.utils import secure_filename

upload_api = api.namespace("api/upload", description="Test API")

ALLOWED_EXTENSIONS = { 'xlsx', 'csv' }


def validate_file(file):
    return True

@upload_api.route('/', methods=['POST'])
class UploadApi(Resource):
    def post(self):
        if 'file' not in request.files:
            abort(406, description="No Files Found")
        
        file = request.files['file']

        if file.filename == '':
            abort(406, description="no file found")
        
        if file and validate_file(file):
            filename = secure_filename(file.filename)
            file.save(os.path.join('/apis', filename))

        data = { 'message': 'file uploaded'}
        return data, 200
