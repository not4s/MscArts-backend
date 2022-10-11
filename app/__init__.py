from flask import Flask
from flask_restx import Api


app = Flask(__name__)
api = Api()

def create_app(test_configuration=None):
    api.init_app(app)
   
    return app