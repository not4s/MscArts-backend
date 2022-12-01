from app.database import db
from sqlalchemy.sql import func


class FileControl(db.Model):
    version = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    timestamp = db.Column(db.DateTime, default=func.now())
    filetype = db.Column(db.String(30))
