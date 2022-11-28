import enum
from app.database import db


class TemplateTab(db.Model):
    # SHA1 10 Character String
    id = db.Column(db.String, primary_key=True, autoincrement=False)
    # Base64 Representation
    base64JSON = db.Column(db.String)
    title = db.Column(db.String, default="")
    default = db.Column(db.Boolean, default=False)
