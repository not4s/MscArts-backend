""" 
taken and modified from edtech/tapp
"""
import itertools
import re
from collections import defaultdict
from typing import Sequence, Optional, Dict, List, Set, Union

import ldap
from ldap.ldapobject import SimpleLDAPObject

from app.protocols import Authenticator

# Used to parse key-value LDAP attributes
ATTRIBUTE_PATTERN = r"([A-Za-z0-9]+)=([A-Za-z0-9-@]+)"
USERNAME_FILTER_TEMPLATE = "(&(objectClass=user)(sAMAccountName=%s))"
BINDING_TEMPLATE = "%s@IC.AC.UK"

# Relevant IC LDAP attributes
TITLE = "extensionAttribute6"
USERNAME = "name"
NAME = "givenName"
SURNAME = "sn"
DN = "distinguishedName"
MEMBER_OF = "memberOf"
MEMBERSHIPS = "memberships"

DOC_CN_MEMBERSHIPS = ("doc-all-students", "doc-staff-group", "doc-ext-group")

# List of attributes to be parsed into dictionaries
ATTRIBUTES_TO_SERIALISE = [DN, MEMBER_OF, MEMBERSHIPS]

RawLdapAttributes = Dict[str, List[bytes]]
SerialisedAttributeValue = Dict[str, Set[str]]
SerialisedAttributes = Dict[str, Union[str, SerialisedAttributeValue]]


class DocLdapAuthenticator(Authenticator):
    """
    The class simplifies the interaction with python-LDAP
    to initialise an LDAPObject and handle the retrieval of
    relevant LDAP user attributes.

    EXAMPLE USAGE FOR LOGIN PURPOSES:
        1. An LDAP object is initialised with LDAP server URL and base distinct name
        2. A new connection is established with connect()
        3. The LDAP binding for a given username and password is performed with ldap_login()
        4. Relevant attributes are queried with query_attributes().
    """

    server_url: str = "ldaps://ldaps-vip.cc.ic.ac.uk:636"
    base_dn: str = "OU=Users,OU=Imperial College (London),DC=ic,DC=ac,DC=uk"

    def _raw_attributes(
        self, username: str, attributes: Sequence[str], connection: SimpleLDAPObject
    ) -> RawLdapAttributes:
        ldap_filter = USERNAME_FILTER_TEMPLATE % username
        raw_res = connection.search(
            self.base_dn, ldap.SCOPE_SUBTREE, ldap_filter, attributes
        )
        res_type, res_data = connection.result(raw_res)
        _, filtered_attributes = res_data[0]
        return filtered_attributes

    def _ldap_authentication(
        self, username: str, password: str, query_attrs: Sequence[str]
    ) -> SerialisedAttributes:
        """
        Performs basic LDAP authentication by binding on a fresh connection with `username` and `password`.
        Throws INVALID_CREDENTIALS exception if authentication fails. On successful authentication,
        retrieves the values stored on the LDAP server associated to `username` for the given `attributes`.
        :param username: username credential
        :param password: password credential
        :param attributes: names of the attributes to filter for
        :return: attr_name -> attr_value dict for given username
        """
        connection = ldap.initialize(self.server_url)
        connection.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_ALLOW)
        connection.set_option(ldap.OPT_X_TLS_NEWCTX, 0)
        connection.simple_bind_s(BINDING_TEMPLATE % username, password)
        attributes = serialise_ldap_attributes(
            self._raw_attributes(username, query_attrs, connection)
        )
        connection.unbind_s()
        return attributes

    def authenticate(self, username: str, password: str) -> Optional[dict]:
        """
        Perform (a) LDAP authentication and (b) additional (DoC specific) verifications
        before granting access and returning relevant user LDAP attributes.
        """
        try:
            ldap_attributes = self._ldap_authentication(
                username,
                password,
                query_attrs=(
                    TITLE,
                    USERNAME,
                    NAME,
                    SURNAME,
                    DN,
                    MEMBER_OF,
                    MEMBERSHIPS,
                ),
            )
            return (
                ldap_attributes
                if validate_affiliation_to_doc(ldap_attributes)
                else None
            )
        except ldap.INVALID_CREDENTIALS:
            return None


LDAP = DocLdapAuthenticator()

###################################################################
# Helpers                                                         #
###################################################################
def validate_affiliation_to_doc(ldap_attributes: dict) -> bool:
    """
    Check if the organisational unit is doc or doc mailing list memberships
    are available.
    """
    if "doc" not in ldap_attributes[DN]["OU"]:
        memberOf = ldap_attributes.get(MEMBER_OF, {}).get("CN", set())
        memberships = ldap_attributes.get(MEMBERSHIPS, {}).get("CN", set())
        return any(
            (doc_cn in (memberOf | memberships) for doc_cn in DOC_CN_MEMBERSHIPS)
        )
    return True


def serialise_ldap_attributes(
    ldap_attributes: RawLdapAttributes,
) -> SerialisedAttributes:
    return {
        k: (
            ldap_attributes_to_dictionary(vs)
            if k in ATTRIBUTES_TO_SERIALISE
            else vs[0].decode("utf-8")
        )
        for k, vs in ldap_attributes.items()
    }


def ldap_attributes_to_dictionary(
    attribute_values: Sequence[bytes],
) -> SerialisedAttributeValue:
    items = (
        re.findall(ATTRIBUTE_PATTERN, item.decode("utf-8").replace(",", " "))
        for item in attribute_values
    )
    d = defaultdict(set)
    for k, v in itertools.chain.from_iterable(items):
        d[k].add(v)
    return d
