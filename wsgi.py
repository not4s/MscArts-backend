from app import create_app
from app.database import db

# APIs
from app.apis.sample import sample_api
from app.apis.program import program_api
from app.apis.upload import upload_api

application = create_app()
