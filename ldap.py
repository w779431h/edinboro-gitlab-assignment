#!/usr/bin/env python3

from ldap3 import Server, Connection, ALL

# Returns the preferred email of the given student
def get_student_email(userid):
    userid = userid[0:8]
    conn = Connection('uwldap.uwaterloo.ca', auto_bind=True)
    conn.search('dc=uwaterloo,dc=ca', '(uid=%s)' % userid, attributes=['mail', 'mailLocalAddress', 'cn'])
    if conn.entries and conn.entries[0].mail:
        return str(conn.entries[0].mail)
    else:
        return "%s@uwaterloo.ca" % userid

# Returns the user id given an @uwaterloo.ca email
def get_userid(email):
    conn = Connection('uwldap.uwaterloo.ca', auto_bind=True)
    conn.search('dc=uwaterloo,dc=ca', '(mailLocalAddress=%s)' % email, attributes=['mail', 'mailLocalAddress', 'cn', 'uid'])
    if conn.entries and conn.entries[0].uid[0]:
        return conn.entries[0].uid[0][0:8]
    else:
        return email[:-len("@uwaterloo.ca")]



# For testing
#print(get_student_email('yc2lee'))
#print(get_userid('yc2lee@uwaterloo.ca'))
