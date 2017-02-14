#!/usr/bin/python3

from ldap3 import Server, Connection, ALL

# Returns the preferred email of the given student
def get_student_email(userid):
    userid = userid[0:8]
    conn = Connection('uwldap.uwaterloo.ca', auto_bind=True)
    conn.search('dc=uwaterloo,dc=ca', '(uid=%s)' % userid, attributes=['mail', 'mailLocalAddress', 'cn'])
    if conn.entries:
        return str(conn.entries[0].mail)
    else:
        return "%s@uwaterloo.ca" % userid

# For testing
#print(get_student_email('jsmio'))
