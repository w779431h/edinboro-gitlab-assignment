#!/usr/bin/env python3

import os
import gitlab
import sys,getpass
import json,urllib.request
from config import host_url

private_token = ''

# request makes a request to host_url/api/v3/
# and returns the JSON data as a Python object
# Input: query: Part of URL after the URL above
#        post_hash: A dictionary of data to send in a POST request
#        query_headers: Any headers you want to send as part of the request
#        quit_on_error: If True, will quit program on error. If False, will
#                       try 2 more times, and finially return false
# Returns: A python object
def request(query, post_hash={}, query_headers={}, http_method=None, quit_on_error=False, max_attempts=3, show_output=True):
    max_tries = 3
    for request_attempt in list(range(1,max_tries+1)):
        try:
            if 'PRIVATE-TOKEN' not in query_headers:
                query_headers['PRIVATE-TOKEN'] = private_token
            post_data = urllib.parse.urlencode(post_hash).encode('ascii') if post_hash else None
            req = urllib.request.Request(url = host_url + "/api/v3/" + query,
                                         data=post_data,
                                         headers=query_headers,
                                         method=http_method)
            with urllib.request.urlopen(req) as f:
                json_string = f.read().decode('utf-8')
                try:
                    python_object = json.loads(json_string)
                except Exception as e:
                    if show_output:
                        print(json_string)
                        print("Error occurred trying to interpret above data as JSON.")
                        print("Error message: %s" % str(e))
                    if quit_on_error:
                        sys.exit(1)
                    else:
                        return False
                return python_object
        except Exception as e:
            if show_output:
                print("Error occurred trying to access " + host_url + "/api/v3/" + query)
                print("Error %s message: %s" % (type(e).__name__, str(e)))
            if quit_on_error:
                sys.exit(1)
            elif request_attempt < max_tries:
                if show_output: print("Retrying... (re-try number %d)" % request_attempt)
    if show_output: print("Request failed after %d attempts" % max_tries)
    return False

# Read private token from token_file. Mutates the global private_token
# above and returns it too.
def set_private_token(token_file):
    global private_token
    if token_file == "/dev/stdin":
        print("You can get your Gitlab private token from " + host_url + "/profile/personal_access_tokens")
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
    print("Could not find group %s." % group_name)
    print("The groups that are available are:")
    name_width = 20
    print(os.linesep)
    print("\t%s   Description" % ("Name".ljust(name_width)))
    print("\t%s   ---------------" % ("-" * name_width))
    for group in groups_data:
        print("\t%s   %s" % (group['name'].ljust(name_width), group['description']))
    print(os.linesep)
    sys.exit(1)



# makes a GitLab object using the `python-gitlab` module
# this function is useful because we use a token file
# takes in the base instance URL, optional private token or token_filename
# it only works if it has a token
# Input:
#     url: GitLab instance URL base address
#     token: a string containing the private token
#     token_filename: the filename of a text file containing the private token
def make_gitlab_obj(url=host_url, token=None, token_filename=None):
    if token_filename:
        try:
            token_file = open(token_filename,"r")
        except Exception as e:
            print("Opening file failed: %s" % e)
            sys.exit(1)
    
        token = str(token_file.readline()).rstrip()
    elif private_token:
        # use token from other function
        token = private_token
    elif not token:
        # TODO: handle no tokens
        # here is a great opportunity to prompt the user
        # for now, just leave it as anonymous API access
        pass
    
    return gitlab.Gitlab(url, private_token=token)

# Helper function for search error handling.
# Raise an error if there are multpile results from a GitLab search
# Input:
#     result: a list containing the search result
#     lst_name: the name of the list, i.e., "users" or "groups"
#     item_name: the name of the item searching for, i.e. "my-class" or "josh"
def bad_search_check(result, lst_name, item_name):
    if len(result) > 1:
        for item in result:
            print(item)
        raise RuntimeError("Multiple %s with name: %s" % (lst_name, item_name))
    elif len(result) == 0:
        raise RuntimeError("No %s found with name: %s" % (lst_name, item_name))
    
    
# returns group object
# Input:
#     gl: the GitLab object
#     name: the name of the group
def get_group_by_name(gl, name):
    # TODO: paginate below list later when there are many groups
    groups = gl.groups.list(search=name)

    # there should only be one group with this name
    bad_search_check(groups, "groups", name)

    return groups[0]


# retrieve a user, given their name
# Input:
#     gl: the GitLab object
#     name: the name of the user
def get_user_by_name(gl, name):
    users = gl.users.list(username=name)

    # there should only be one user with this name
    bad_search_check(users, "users", name)

    return users[0]


# retrieve a project, given its name
# Input:
#     gl: the GitLab object
#     name: the name of the project
#     g_name: the name of the group
def get_project_by_name(gl, name, g_name=None):
    projects = None
    if g_name:
        group = get_group_by_name(gl, g_name)

        # get the project by its name
        projects = group.projects.list(search=name)
    else:
        projects = gl.projects.list(search=name)

    # bad_search_check(projects, "projects", name)

    return projects[0]


# add users to a group
# adds users from a list of usernames to a group
# this is mainly a test function
# Input:
    # gl: the GitLab object
    # g_name: the name of the group to add to
    # new_users: list of new users to add
def add_users_to_group(gl, g_name, new_users):
    try:
        group = get_group_by_name(gl, g_name)
    except RuntimeError as e:
        print("Finding group failed with name: %s" % e)
        sys.exit(1)
        
    for username in new_users:
        # print(get_user_by_name(gl, username))
        user = get_user_by_name(gl, username)
        try:
            group.members.create({'user_id': user.id,
                                  'access_level': gitlab.DEVELOPER_ACCESS})
            print("User %s added to group %s" % (user.name, group.name))
        except gitlab.exceptions.GitlabCreateError as e:
            # The expected error is "error 409: Member already exists"
            # Just keep going
            print("Encountered error: %s\nContinuing" % e)

# add a user to a project in a given group
# Input:
#     gl: the GitLab object
#     user_id: the user ID of the new project member. It's an integer
#     proj_name: the project name
#     g_name: the group name, if the project is in a group
def add_user_to_project(gl, user_id, proj_name, g_name=None):
    group_project = get_project_by_name(gl, proj_name, g_name=g_name)

    # convert GroupProject object to Project, so we can see its members
    project = gl.projects.get(group_project.id)

    # print("Student user id is %s" % user_id) # checking student id
    # print(project.members.list(),project.name) # .members checking
    project.members.create({'user_id': user_id,
                            'access_level': gitlab.DEVELOPER_ACCESS})
