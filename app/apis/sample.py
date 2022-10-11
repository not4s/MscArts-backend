from app import api
from flask_restx import Resource

sample_api = api.namespace("sample", description="Test API")

@sample_api.route('/', methods=['GET'])
class TestApi(Resource):
    def get(self):
        return { 'message': 'hello!' }
