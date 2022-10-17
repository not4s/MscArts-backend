from admissions.utils import ldap
from jwt import DecodeError, ExpiredSignatureError, InvalidSignatureError
from flask_jwt_extended.exceptions import InvalidHeaderError, JWTDecodeError, NoAuthorizationError, RevokedTokenError
from admissions.utils.credentials import Roles, getRoles
from functools import wraps

from flask import request, abort
from flask.json import jsonify
from flask_restx import Resource
from flask_jwt_extended import (
    jwt_required,
    verify_jwt_in_request,
    get_jwt_claims,
    create_access_token,
)

from werkzeug.security import check_password_hash

from admissions import api, jwt, db
from admissions.models.session import Credentials

user_api = api.namespace("api/user", description="Login and role operations")


# Defines data stored per access token (called on create_access_token)
@jwt.user_claims_loader
def add_claims_to_access_token(user):
    return user


# Defines identity of user as the user's email (called on create_access_token)
@jwt.user_identity_loader
def user_identity_lookup(user):
    return user["username"]


# Error handlers
@user_api.errorhandler(DecodeError)
def handle_expiration_exception(error):
    return {"message": "The token could not be decoded."}, 401


@user_api.errorhandler(JWTDecodeError)
def handle_expiration_exception(error):
    return {"message": "The token could not be decoded."}, 401


@user_api.errorhandler(InvalidSignatureError)
def handle_expiration_exception(error):
    return {"message": "The token is invalid."}, 401


@user_api.errorhandler(ExpiredSignatureError)
def handle_expiration_exception(error):
    return {"message": "The token has expired."}, 401


@user_api.errorhandler(RevokedTokenError)
def handle_expiration_exception(error):
    return {"message": "The token has expired."}, 401


@user_api.errorhandler(NoAuthorizationError)
def handle_no_jwt_exception(error):
    return {"message": "No bearer token found."}, 401


@user_api.errorhandler(InvalidHeaderError)
def handle_no_jwt_exception(error):
    return {"message": "The header is invalid."}, 401


def applicant_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt_claims()
        if Roles.applicant not in claims["roles"]:
            return {"message": "Applicants Only!"}, 403
        else:
            return fn(*args, **kwargs)

    return wrapper


def question_setter_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt_claims()
        if Roles.question_setter not in claims["roles"]:
            return {"message": "Question Setters Only!"}, 403
        else:
            return fn(*args, **kwargs)

    return wrapper


def quiz_admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt_claims()
        if Roles.test_admin not in claims["roles"]:
            return {"message": "Test Admins Only!"}, 403
        else:
            return fn(*args, **kwargs)

    return wrapper


def sys_admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt_claims()
        if Roles.system_admin not in claims["roles"]:
            return {"message": "System Admins Only!"}, 403
        else:
            return fn(*args, **kwargs)

    return wrapper


@user_api.route("/login", methods=["POST"])
class UserLogin(Resource):
    def post(self):
        if not request.is_json:
            abort(406, description="MIME type is required to be application/json.")

        user = request.json
        username = user.get("username", None).strip()
        password = user.get("password", None)
        credentials = Credentials.query.get_or_404(username)

        if credentials.is_imperial:
            user_ldap_attributes = ldap.login(username, password)
            valid = user_ldap_attributes is not None
        else:
            valid = check_password_hash(credentials.password, password)

        response = {}
        if valid:
            response["success"] = True

            roles = getRoles(db, username)
            response["roles"] = roles

            identity = dict(username=username, roles=roles, is_imperial=credentials.is_imperial)
            response["accessToken"] = create_access_token(identity=identity)
            response = jsonify(response)
            response.status_code = 200
        else:
            response["success"] = False
            response = jsonify(response)            
            response.status_code = 403

        return response


@user_api.route("/roles", methods=["GET"])
class UserRoles(Resource):
    @jwt_required
    def get(self):
        claims = get_jwt_claims()
        roles = claims["roles"]
        return roles, 200
