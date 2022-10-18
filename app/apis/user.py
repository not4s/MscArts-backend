from app import api, ldap_service
from app.database import db
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

from app.models.user_access import UserAccess
from app.utils.user_access import getAccessLevel, addUser

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
        if claims["role"] >= 3:
            return fn(*args, **kwargs)
        else:
            return {"message": "System Admins Only!"}, 403

    return wrapper


def write_access_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if claims["role"] >= 2:
            return fn(*args, **kwargs)
        else:
            return {"message": "No Write Access"}, 403

    return wrapper


def read_access_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if claims["role"] >= 1:
            return fn(*args, **kwargs)
        else:
            return {"message": "No Read Access"}, 403

    return wrapper


@user_api.route("/login", methods=["POST"])
class UserLogin(Resource):
    def post(self):
        if not request.is_json:
            abort(406, description="MIME type is required to be application/json.")

        user = request.json
        username = user.get("username", None).strip()
        password = user.get("password", None)

        if username is None or password is None:
            return {"message": "Missing username or password"}, 400

        user_ldap_attributes = ldap_service.authenticate(username, password)
        valid = user_ldap_attributes is not None

        response = {}
        if valid:
            response["success"] = True
            identity = dict(username=username, is_imperial=True)

            role = getAccessLevel(username)

            if role is None:
                addUser(db, username)
                return {"message": "Request permission from a system admin"}, 401

            if role[0].access == 0:
                return {"message": "Request permission from a system admin"}, 401

            response["accessToken"] = create_access_token(
                identity=identity, additional_claims={"role": role[0].access}
            )
            response = jsonify(response)
            response.status_code = 200
        else:
            response["success"] = False
            response = jsonify(response)
            response.status_code = 403

        return response


@user_api.route("/roles", methods=["GET", "DELETE", "PUT"])
class UserRoles(Resource):
    @jwt_required()
    def get(self):
        claims = get_jwt()
        roles = claims["role"]
        return roles, 200

    @jwt_required()
    @admin_required
    def delete(self):

        username = request.json.get("username", None)

        if username is None:
            return {"message": "No username provided"}, 400

        user = UserAccess.query.filter_by(username=username).first()

        if user is None:
            return {"message": "No user found"}, 200

        db.session.delete(user)
        db.session.commit()
        return {"message": "Successfully deleted user"}, 200

    @jwt_required()
    @admin_required
    def put(self):
        username = request.json.get("username", None)
        access = request.json.get("access", None)

        if username is None or access is None:
            return {"message": "No username or access provided"}, 400

        requester_access = get_jwt()["role"]

        if requester_access < access:
            return {"message": "Unable to grant higher access than requester"}, 401

        user = UserAccess.query.filter_by(username=username).first()

        if user is None:
            addUser(db, username, access)
            return {"message": "Successfully added new user access"}, 200

        if user.access > requester_access:
            return {"message": "Unable to alter user with higher access level"}, 401

        user.access = access
        db.session.commit()
        return {"message": "Successfully updated user access"}, 200
