from app import api
from app.database import db
from app.models.template import TemplateTab
from app.schemas.template import TemplateTabSchema
from app.apis.user import read_access_required, write_access_required
from flask_jwt_extended import get_jwt
from flask import request, abort
from flask_restx import Resource
import hashlib

template_api = api.namespace("api/template", description="Template API")

template_tab_deserializer = TemplateTabSchema()


@template_api.route("/", methods=["GET", "POST"])
class TemplateTabAPI(Resource):
    @read_access_required
    def get(self):
        template_id = request.args.get("id", default=None, type=str)

        template = TemplateTab.query.filter_by(id=template_id).first()

        return {"base64JSON": template.base64JSON, "title": template.title}, 200

    @read_access_required
    def post(self):
        if not request.is_json:
            abort(406, description="MIME type is required to be application/json.")

        body = request.json

        template_base64 = body.get("base64JSON", None)

        if template_base64 is None:
            return {"message": "Malformed Request"}, 400

        hash_obj = hashlib.sha1(str.encode(template_base64))
        hash_id = hash_obj.hexdigest()[:16]

        template = TemplateTab.query.filter_by(id=hash_id).first()

        if template is not None:
            return {"id": template.id}, 200

        new_template = TemplateTab(id=hash_id, base64JSON=template_base64)

        db.session.add(new_template)
        db.session.commit()

        return {"id": hash_id}, 200


@template_api.route("/default/", methods=["GET", "POST", "DELETE", "PUT"])
class DefaultTemplateAPI(Resource):
    @write_access_required
    def get(self):
        query = TemplateTab.query.filter_by(default=True)

        return [template_tab_deserializer.dump(d) for d in query.all()], 200

    @write_access_required
    def delete(self):
        if not request.is_json:
            abort(406, description="MIME type is required to be application/json.")

        body = request.json

        uid = body.get("uid", None)

        if uid is None:
            return {"message": "Malformed Request"}, 400

        try:
            TemplateTab.query.filter_by(id=uid).delete()
            db.session.commit()
            return {"message": "Deleted"}, 200
        except Exception as e:
            return {"message": "Could not delete"}, 200

    @write_access_required
    def post(self):
        if not request.is_json:
            abort(406, description="MIME type is required to be application/json.")

        body = request.json

        uid = body.get("uid", None)
        title = body.get("title", None)

        if uid is None or title is None:
            return {"message": "Malformed Request"}, 400

        template = TemplateTab.query.filter_by(id=uid).first()

        if template is None:
            return {"message": "Template UID not found"}, 400

        template.default = True
        template.title = title
        db.session.commit()

        return {"message": "Added new default template"}, 200

    @write_access_required
    def put(self):
        if not request.is_json:
            abort(406, description="MIME type is required to be application/json.")

        body = request.json

        uid = body.get("uid", None)
        title = body.get("title", None)

        if uid is None or title is None:
            return {"message": "Malformed Request"}, 400

        template = TemplateTab.query.filter_by(id=uid).first()

        if template is None:
            return {"message": "Template UID not found"}, 400

        template.title = title
        db.session.commit()

        return {"message": "Edited default template"}, 200
