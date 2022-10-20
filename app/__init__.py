import os

from flask import Flask
from flask_cors import CORS
from flask_restx import Api
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager

from .database import db, db_migrator

configuration_switch = {
    "dev": f"{__name__}.config.DevConfig",  # Development configuration (fake LDAP)
    "staging": f"{__name__}.config.StagingConfig",  # Staging configuration (should be as close as possible to prod)
    "production": f"{__name__}.config.ProductionConfig",  # Production configuration
}

environment = os.environ.get("ENV", "dev")


app = Flask(__name__)
app.config.from_object(configuration_switch[environment])
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
app.config["CORS_HEADERS"] = "Content-Type"
jwt = JWTManager(app)
api = Api()
ma = Marshmallow()

ldap_service = app.config["LDAP_SERVICE"]


def create_app(test_configuration=None):

    api.init_app(app)
    db.init_app(app)
    ma.init_app(app)

    with app.app_context():
        db_migrator.init_app(
            app,
            db,
            compare_type=True,
            render_as_batch=db.engine.url.drivername == "sqlite",
        )

        db.create_all()

    return app
