from app.database import db


class UserAccess(db.Model):
    username = db.Column(db.String, primary_key=True)
    access = db.Column(db.Integer, default=0)
