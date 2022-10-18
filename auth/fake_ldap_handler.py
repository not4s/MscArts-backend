from app.protocols import Authenticator


class FakeLdapAuthenticator(Authenticator):
    def authenticate(self, username, password):
        test_users = {"admin", "writer", "reader", "no_access"}
        if username not in test_users:
            return None
        return username


FAKE_LDAP = FakeLdapAuthenticator()
