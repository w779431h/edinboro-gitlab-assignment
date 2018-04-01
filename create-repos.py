#!/usr/bin/env python3

import time
import argparse,getpass,re
import sys,subprocess,os
import json,urllib.request
import emailboro
import simple_gitlab
import gitlab # external module python-gitlab
from config import host_url, host_url_just_fqdn

# Parse command-line arguments.
parser = argparse.ArgumentParser(description="This script is used to create student repositories.")
parser.add_argument('group_name', help="The name of the Gitlab group to create projects in.")
parser.add_argument('--token-file', default="/dev/stdin",
                    help="Path to file containing your Gitlab private token. Default is to read from standard input.")
parser.add_argument('--cookie-file', default="/dev/stdin",
                    help="Path to file containing your Gitlab _gitlab_session cookie value. Default is to read from standard input.")
parser.add_argument('--add-students', action='store_true',
                    help="By default, students will not be added to their repos. Set this option to add them, which will email them too.")
students_arg_group = parser.add_mutually_exclusive_group()
students_arg_group.add_argument('--classlist', nargs=1, help="Path to your course's .classlist file on the student.cs Linux servers.")
students_arg_group.add_argument('--students', help="A comma separated list of student Quest IDs. Create repositories for these students only.")
args = parser.parse_args()

# save command line argument inputs in variables
group_name = args.group_name
token_file = args.token_file
add_students = args.add_students
cookie_file = args.cookie_file

# Read private token from keyboard or from file
simple_gitlab.set_private_token(token_file)

# Students we will create repositories for
students = []
if args.students:
    students = list(map(lambda s:s.strip(), args.students.split(',')))
    students = list(filter(lambda s: s and not s.isspace(), students))
    students = list(map(lambda s:s[:8],students))
elif args.classlist:
    classlist_regex = re.compile('[a-z]{2}[0-9]{6}')
    classlist_file = args.classlist[0]
    for line in open(classlist_file, 'r'):
        match = classlist_regex.match(line)
        if match != None:
            userid = match.group(0)
            userid = userid[0:8]
            students.append(userid)

# Create a hash mapping student usernames to the id of their project/repo
# This should be empty. If not, it means some projects have already
# been created.
group_id = simple_gitlab.get_group_id(group_name)
group_data = simple_gitlab.request("groups/%d" % group_id)
projects_data = group_data['projects']
project_ids = {}
for project in projects_data:
    username = project['ssh_url_to_repo'].rsplit('/',1)[-1][:-4]
    project_ids[username] = project['id']

# Begin processing students
print("Processing %d total students." % len(students))
for student in students:
    print(os.linesep)
    print('-' * 60)
    print("> Processing %s" % student)
    
    # Create project/repo for students who do not have one yet.
    if student not in project_ids:
        # Student doesn't have a project/repo yet. Create it
        print("> %s doesn't have a project/repo yet. Creating it now." % student)
        new_project = simple_gitlab.request('projects', post_hash={'name':student, 'namespace_id':group_id, 'visibility_level':0})
        project_ids[student] = new_project['id']
        print("> Created new project with id %d" % new_project['id'])
    else:
        print("> %s already has a project (id %d). Not creating it again." % (student, project_ids[student]))

    # Create master branch if it doesn't exist yet
    existing_branches = simple_gitlab.request('projects/%d/repository/branches' % project_ids[student])
    master_branch_exists = False
    for branch in existing_branches:
        if branch['name'] == 'master':
            master_branch_exists = True
    if not master_branch_exists:
        print("> master branch doesn't exist for %s. Creating it." % student)
        time.sleep(3)
        for assn in ['A0', 'A1', 'A2', 'A3', 'A4']:
            print("> Doing work for assignment %s" % assn)
            simple_gitlab.request('projects/%d/repository/files' % project_ids[student],
                           post_hash={'file_path':("%s/.gitignore" % assn), 'branch_name':"master", 'content':"*.class\n", 'commit_message':("Creating %s folder" % assn)})

        # Wait for master branch to become protected. Gitlab seems to have a delay on protecting the
        # master branch when it's created.
        while True:
            master_branch_info = simple_gitlab.request('/projects/%d/repository/branches/master' % project_ids[student], quit_on_error=False)
            if master_branch_info and master_branch_info['protected']:
                print("> Newly created master branch has become protected.")
                break
            print("> Waiting for Gitlab to make newly created master branch protected.")
            time.sleep(1) # Don't spam Gitlab website
    else:
        print("> master branch already exists for %s. Not creating it." % student)

    # Turn off master branch protection (on by default). At this point
    # in the code, we have created master branch if it doesn't exist.
    # So master branch should exist. Also, if master is already unprotected,
    # then this operation does nothing (it's idempotent).

    # print("> Unprotecting master branch.")
    # simple_gitlab.request('/projects/%d/repository/branches/master/unprotect' % project_ids[student], http_method='PUT')
        
    # The repo is now set up with an unprotected master branch.
    # Do email invitation if user wants to do that.
    if add_students:

        print("> Connecting to GitLab.")

        # TODO: figure out token filename 
        gl = simple_gitlab.make_gitlab_obj(token_filename="test_token")
        try:
            current_group = gl.groups.get(group_id)
        except Exception as e:
            print("Encountered error %s!" % e)
            print("> Could not find group with ID %s!" % group_id)

        print("> Adding student to project/repository.")

        # the project name will be the student's username, so get that
        # proj_name = None
        # try:
        #     proj_name = simple_gitlab.get_user_by_name(gl, student).username
        # except Exception as e:
        #     print("Encountered error `%s` while finding user" % e)
        #     print("> Could not add student %s to repo!" % student)

        student_id = simple_gitlab.get_user_by_name(gl, student).id
        # try:
        simple_gitlab.add_user_to_project(gl, student_id, student, \
                                              g_name=current_group.name)
        print("Student added as member of %s/student." % (current_group.name, student))
        # except Exception as e:
        #     print("Encountered error `%s` while adding user" % e)
        #     print("> Could not add student %s to repo!" % student)


    print("> Done processing %s." % student)
    time.sleep(5) # Put in a bit of a delay so that codestore.cs.edinboro.edu isn't hammered
