import os
from auth import fake_ldap_handler, ldap_handler
from datetime import timedelta


class BaseConfig:
    # JWT ======================================================
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=4)
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "mscarts")

    # LDAP Service =============================================
    LDAP_SERVICE = fake_ldap_handler.FAKE_LDAP

    # Database ===================================================
    SQLALCHEMY_TRACK_MODIFICATIONS = True


class DevConfig(BaseConfig):
    # Database ===================================================
    SQLALCHEMY_DATABASE_URI = "sqlite:///dev.db"


class StagingConfig(BaseConfig):
    # LDAP Service =============================================
    LDAP_TYPE = os.environ.get("DUMMY_LDAP", None)
    LDAP_SERVICE = (
        ldap_handler.LDAP if LDAP_TYPE is None else fake_ldap_handler.FAKE_LDAP
    )

    # Database ===================================================
    STAGING_DB_HOST = os.environ.get("STAGING_DB_HOST", None)
    STAGING_DB = os.environ.get("STAGING_DB", None)
    STAGING_DB_USER = os.environ.get("STAGING_DB_USER", None)
    STAGING_DB_PASSWORD = os.environ.get("STAGING_DB_PASSWORD", None)

    if (
        STAGING_DB_PASSWORD is not None
        and STAGING_DB_USER is not None
        and STAGING_DB is not None
        and STAGING_DB_HOST is not None
    ):
        SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg2://{STAGING_DB_USER}:{STAGING_DB_PASSWORD}@{STAGING_DB_HOST}:5432/{STAGING_DB}"
    else:
        SQLALCHEMY_DATABASE_URI = "sqlite:///staging.db"
