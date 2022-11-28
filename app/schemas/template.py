from app import ma
from app.models.template import TemplateTab


class TemplateTabSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = TemplateTab
