#!/usr/bin/python3

import time
import argparse,getpass,re
import sys,subprocess,os
import json,urllib.request
import gitlab

# Parse command-line arguments.
parser = argparse.ArgumentParser(description="This script is used to create student repositories.")
parser.add_argument('group_name', help="The name of the Gitlab group to create projects in.")
parser.add_argument('--token-file', default="/dev/stdin",
                    help="Path to file containing your Gitlab private token. Default is to read from standard input.")
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

# Read private token from keyboard or from file
gitlab.set_private_token(token_file)

# If adding students, read gitlab session cookie
if add_students:
    print("You want students to be added to their project/repository.")
    print("This script adds students by interfacing with the git.uwaterloo.ca website directly.")
    print("Please login to https://git.uwaterloo.ca and enter your _gitlab_session cookie from git.uwaterloo.ca below.")
    gitlab_session_cookie = getpass.getpass("git.uwaterloo.ca _gitlab_session cookie value:")

# Students we will create repositories for
students = []
if args.students:
    students = list(map(lambda s:s.strip(), args.students.split(',')))
    students = list(filter(lambda s: s and not s.isspace(), students))
elif args.classlist:
    classlist_regex = re.compile('^[0-9]{8}:([a-z0-9]+):')
    classlist_file = args.classlist[0]
    for line in open(classlist_file, 'r'):
        match = classlist_regex.match(line)
        if match != None:
            userid = match.group(1)
            userid = userid[0:8]
            students.append(userid)

# Create a hash mapping student usernames to the id of their project/repo
# This should be empty. If not, it means some projects have already
# been created.
group_id = gitlab.get_group_id(group_name)
group_data = gitlab.request("groups/%d" % group_id)
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
        new_project = gitlab.request('projects', post_hash={'name':student, 'namespace_id':group_id, 'visibility_level':0})
        project_ids[student] = new_project['id']
        print("> Created new project with id %d" % new_project['id'])
    else:
        print("> %s already has a project (id %d). Not creating it again." % (student, project_ids[student]))

    # Create master branch if it doesn't exist yet
    existing_branches = gitlab.request('projects/%d/repository/branches' % project_ids[student])
    master_branch_exists = False
    for branch in existing_branches:
        if branch['name'] == 'master':
            master_branch_exists = True
    if not master_branch_exists:
        print("> master branch doesn't exist for %s. Creating it." % student)
        for assn in ['A0', 'A1', 'A2', 'A3', 'A4']:
            print("> Doing work for assignment %s" % assn)
            gitlab.request('projects/%d/repository/files' % project_ids[student],
                           post_hash={'file_path':("%s/.gitignore" % assn), 'branch_name':"master", 'content':"*.class\n", 'commit_message':("Creating %s folder" % assn)})
            time.sleep(5)

        # Wait for master branch to become protected. Gitlab seems to have a delay on protecting the
        # master branch when it's created.
        while True:
            master_branch_info = gitlab.request('/projects/%d/repository/branches/master' % project_ids[student], quit_on_error=False)
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
    print("> Unprotecting master branch.")
    gitlab.request('/projects/%d/repository/branches/master/unprotect' % project_ids[student], http_method='PUT')
        
    # The repo is now set up with an unprotected master branch.
    # Do email invitation if user wants to do that.
    if add_students:
        print("> Adding student to project/repository.")

        # Step 1: Go to project_members web page and get authenticity token.
        print("> Getting authenticity token from project_members page.")
        authenticity_token = None
        req = urllib.request.Request("https://git.uwaterloo.ca/%s/%s/project_members" % (group_name, student),
                                     headers={'Cookie': "_gitlab_session=%s"%gitlab_session_cookie})
        with urllib.request.urlopen(req) as f:
            project_members_html = f.read().decode('utf-8')
            for line in project_members_html.splitlines():
                match = re.search(r'<input type="hidden" name="authenticity_token" value="([^"]+)" />', line)
                if match:
                    authenticity_token = match.group(1)
                    break

        # Step 2: Make the post request to invite by email
        if authenticity_token:
            student_email = "%s@uwaterloo.ca" % student
            print("> Got authenticity token.")
            print("> Sending invitation email to %s" % student_email)
            post_data = urllib.parse.urlencode({'authenticity_token':authenticity_token,'user_ids':student_email,'access_level':30}).encode('ascii')
            add_student_post = urllib.request.Request("https://git.uwaterloo.ca/%s/%s/project_members" % (group_name, student),
                                                      headers={'Cookie': "_gitlab_session=%s"%gitlab_session_cookie},
                                                      data=post_data, method='POST')
            urllib.request.urlopen(add_student_post)
        else:
            print("> Could not add student %s to repo!" % student)

    print("> Done processing %s." % student)
    time.sleep(10) # Put in a bit of a delay so that git.uwaterloo.ca isn't hammered
