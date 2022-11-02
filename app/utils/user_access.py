from app import app
from app.models.user_access import UserAccess


def getAccessLevel(username):
    if app.config.get("LDAP_TYPE", None) is not None:
        if username == "no_access":
            access = 0
        if username == "reader":
            access = 1
        elif username == "writer":
            access = 2
        elif username == "admin":
            access = 3
        else:
            user = UserAccess.query.filter(UserAccess.username == username).all()
            return user if user != [] else None

        return [UserAccess(username=username, access=access)]

    user = UserAccess.query.filter(UserAccess.username == username).all()
    return user if user != [] else None


def addUser(db, username, access=0):
    new_user = UserAccess(username=username, access=access)
    db.session.add(new_user)
    db.session.commit()
