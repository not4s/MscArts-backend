from app.database import db

class SampleData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer, default=0)
    test = db.Column(db.String(120))