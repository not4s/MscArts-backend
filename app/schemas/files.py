from app import ma
from app.models.files import FileControl


class FileControlSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = FileControl
