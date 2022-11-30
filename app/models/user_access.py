from app.database import db
from sqlalchemy import event

class UserAccess(db.Model):
    username = db.Column(db.String, primary_key=True)
    access = db.Column(db.Integer, default=0)
    layout = db.Column(db.String, default="")

# On initialisation of the app, inserts default usernames in the db
@event.listens_for(UserAccess.__table__, 'after_create')
def create_users(*args, **kwargs):
    db.session.add(UserAccess(username='admin', access='3'))
    db.session.add(UserAccess(username='write', access='2'))
    db.session.add(UserAccess(username='read', access='1'))
    db.session.add(UserAccess(username='no_access', access='0'))
    db.session.commit()