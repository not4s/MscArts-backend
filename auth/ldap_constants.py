""" 
taken and modified from edtech/tapp
"""

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