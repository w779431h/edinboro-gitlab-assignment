#!/usr/bin/python3

import sys,getpass
import json,urllib.request

private_token = ''

# request makes a request to https://git.uwaterloo.ca/api/v3/
# and returns the JSON data as a Python object
# Input: query: Part of URL after the URL above
#        post_hash: A dictionary of data to send in a POST request
#        query_headers: Any headers you want to send as part of the request
#        quit_on_error: If True, will quit program on error. If False, will
#                       return False on error instead
# Returns: A python object
def request(query, post_hash={}, query_headers={}, http_method=None, quit_on_error=True):
    try:
        if 'PRIVATE-TOKEN' not in query_headers:
            query_headers['PRIVATE-TOKEN'] = private_token
        post_data = urllib.parse.urlencode(post_hash).encode('ascii') if post_hash else None
        req = urllib.request.Request(url="https://git.uwaterloo.ca/api/v3/" + query,
                                     data=post_data,
                                     headers=query_headers,
                                     method=http_method)
        with urllib.request.urlopen(req) as f:
            json_string = f.read().decode('utf-8')
            try:
                python_object = json.loads(json_string)
            except Exception as e:
                print(json_string)
                print("Error occurred trying to interpret above data as JSON.")
                print("Error message: %s" % str(e))
                if quit_on_error:
                    sys.exit(1)
                else:
                    return False
            return python_object
    except Exception as e:
        print("Error occurred trying to access https://git.uwaterloo.ca/api/v3/" + query)
        print("Error %s message: %s" % (type(e).__name__, str(e)))
        if quit_on_error:
            sys.exit(1)
        else:
            return False

# Read private token from token_file. Mutates the global private_token
# above and returns it too.
def set_private_token(token_file):
    global private_token
    if token_file == "/dev/stdin":
        print("You can get your Gitlab private token from https://git.uwaterloo.ca/profile/account")
        private_token = getpass.getpass("Please enter your Gitlab private token:")
        return private_token
    else:
        try:
            token_file_handle = open(token_file, 'r')
            private_token = token_file_handle.readline().strip()
            token_file_handle.close()
            return private_token
        except Exception as e:
            print("Error occurred trying to read private token from file %s" % token_file)
            print("Error message: %s" % str(e))
            sys.exit(1)

# Returns the group id (an integer) of group_name. If group_name could
# not be found, prints the groups available and exit.
def get_group_id(group_name):
    groups_data = request('groups')
    for group in groups_data:
        if group['name'] == group_name:
            return group['id']
    # could not find a group with the given name
    print("Could not find group %s." % group_to_clone)
    print("The groups that are available are:")
    name_width = 20
    print(os.linesep)
    print("\t%s   Description" % ("Name".ljust(name_width)))
    print("\t%s   ---------------" % ("-" * name_width))
    for group in groups_data:
        print("\t%s   %s" % (group['name'].ljust(name_width), group['description']))
    print(os.linesep)
    sys.exit(1)
