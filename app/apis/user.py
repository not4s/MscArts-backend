from app import api, ldap_service
from jwt import DecodeError, ExpiredSignatureError, InvalidSignatureError
from flask_jwt_extended.exceptions import (
    InvalidHeaderError,
    JWTDecodeError,
    NoAuthorizationError,
    RevokedTokenError,
)
from functools import wraps

from flask import request, abort
from flask.json import jsonify
from flask_restx import Resource
from flask_jwt_extended import (
    get_jwt,
    jwt_required,
    verify_jwt_in_request,
    create_access_token,
)


user_api = api.namespace("api/user", description="Login and role operations")

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


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if "admin" != claims["role"]:
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

        user_ldap_attributes = ldap_service.authenticate(username, password)
        valid = user_ldap_attributes is not None

        response = {}
        if valid:
            response["success"] = True
            identity = dict(username=username, is_imperial=True)

            # [TODO] Role Control
            role = {"role": "student"}

            response["accessToken"] = create_access_token(
                identity=identity, additional_claims=role
            )
            response = jsonify(response)
            response.status_code = 200
        else:
            response["success"] = False
            response = jsonify(response)
            response.status_code = 403

        return response


@user_api.route("/roles", methods=["GET"])
class UserRoles(Resource):
    @jwt_required()
    def get(self):
        claims = get_jwt()
        roles = claims["role"]
        # roles = {"message": "all good"}
        return roles, 200


@user_api.route("/admin", methods=["GET"])
class AdminAPI(Resource):
    @jwt_required()
    @admin_required
    def get(self):
        return {"message": "Hello World"}, 200
