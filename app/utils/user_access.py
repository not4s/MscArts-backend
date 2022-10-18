from app.models.user_access import UserAccess


def getAccessLevel(username):
    user = UserAccess.query.filter(UserAccess.username == username).all()
    return user if user != [] else None


def addUser(db, username, access=0):
    new_user = UserAccess(username=username, access=access)
    db.session.add(new_user)
    db.session.commit()
