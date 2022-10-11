from app import api
from app.database import db 
from flask import request, abort
from flask_restx import Resource

# Database
from app.models.example import SampleData
from app.schemas.example import SampleDataSchema

sample_api = api.namespace("sample", description="Test API")

sample_data_serializer = SampleDataSchema()


@sample_api.route('/', methods=['GET', 'POST'])
class TestApi(Resource):
    def get(self):
        data = SampleData.query.all()
        result = [sample_data_serializer.dump(d) for d in data]
        return result, 200

    def post(self):
        if not request.is_json:
            abort(406, description="NOT JSON")

        # print(request.json["count"])
        data = { 'message': 'in progress' }

        new_sample_data = SampleData(count=request.json["count"])
        db.session.add(new_sample_data)
        db.session.commit()
        return data, 200
