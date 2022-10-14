import os

class BaseConfig:
    # Database ===================================================
    SQLALCHEMY_TRACK_MODIFICATIONS = True


class DevConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = "sqlite:///dev.db"


class StagingConfig(BaseConfig):
    STAGING_DB = os.environ.get("STAGING_DB", None)
    STAGING_DB_USER = os.environ.get("STAGING_DB_USER", None)
    STAGING_DB_PASSWORD = os.environ.get("STAGING_DB_PASSWORD", None)

    if STAGING_DB_PASSWORD is not None and STAGING_DB_USER is not None and STAGING_DB is not None:
        SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg2://{STAGING_DB_USER}:{STAGING_DB_PASSWORD}@db.doc.ic.ac.uk:5432/{STAGING_DB}"
    else:
        SQLALCHEMY_DATABASE_URI = "sqlite:///staging.db"
        
