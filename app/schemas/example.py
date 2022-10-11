from app import ma
from app.models.example import SampleData

class SampleDataSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = SampleData