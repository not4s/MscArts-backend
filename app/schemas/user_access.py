from app import ma
from app.models.user_access import UserAccess

class UserAccessSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = UserAccess