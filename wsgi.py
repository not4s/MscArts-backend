from app import create_app
from app.database import db

# APIs
from app.apis.sample import sample_api

app = create_app()