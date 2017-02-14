#!/usr/bin/python3

import time
import argparse,getpass,re
import sys,subprocess,os
import json,urllib.request,csv
import gitlab
import ldap

# Returns a list of the items that occur multiple times in set_of_sets
def find_duplicates(set_of_sets):
    seen = set()
    duplicates = set()
    for aset in set_of_sets:
        for item in aset:
            if item in seen:
                duplicates.add(item)
            else:
                seen.add(item)
    return sorted(list(duplicates))


#
# Parse command-line arguments.
#
parser = argparse.ArgumentParser(description="This script is used to create student repositories for cs447/ece453/se465.")
parser.add_argument('group_name', help="The name of the Gitlab group to create projects in.")
parser.add_argument('membership_file', help="Path to a CSV containing group memberships, with fields: Timestamp, WatIAM user id for member 1, WatIAM user id for member 2 (optional), WatIAM user id for member 3 (optional), Group number (optional)")
parser.add_argument('--token-file', default="/dev/stdin",
                    help="Path to file containing your Gitlab private token. Default is to read from standard input.")
parser.add_argument('--current-membership', action='store_true',
                    help="Prints the current group memberships according to git.uwaterloo.ca and quit.")
parser.add_argument('--check-membership', action='store_true',
                    help="Checks the membership_file against the current group memberships. Prints any problems it finds and quit.")
args = parser.parse_args()


#
# Save command line argument inputs in variables for readability
#
group_name = args.group_name
membership_file = args.membership_file
token_file = args.token_file
print_current_membership = args.current_membership
check_membership = args.check_membership


#
# Read the group membership info from the input CSV file, and store them in sets. Each set stores sets of WatIAM ids.
# One set stores all the groups, the other set only stores the groups we have to create (rows in CSV file without
# line numbers)
#
all_file_memberships = set()
groups_to_create = set()
try:
    with open(membership_file) as csvfile:
        reader = csv.reader(csvfile)
        # Skip over header line
        reader.__next__()
        for row in reader:
            if str.isdigit(row[-1]):
                # This row ends with a group number. Don't need to recreate it.
                all_file_memberships.add(frozenset(filter(None, map(str.strip, row[1:-1]))))
            else:
                # Need to create new project
                to_add = frozenset(filter(None, map(str.strip, row[1:])))
                all_file_memberships.add(to_add)
                groups_to_create.add(to_add)
except Exception as e:
    sys.stderr.write("Error occured while processing membership file %s:\n" % membership_file)
    sys.stderr.write(str(e) + "\n")
    sys.exit(1)


#
# Read private gitlab token from keyboard or from file
#
gitlab.set_private_token(token_file)


#
# Get group id (internal gitlab database number not visible from web interface). Also get the list
# of projects. We need the list so that we can find the highest project number (we'll name projects
# as a random number)
#
group_id = gitlab.get_group_id(group_name)
print("Getting list of projects in group %s... " % group_name, end='', flush=True)
group_data = gitlab.request("groups/%d" % group_id)
print("Done.", flush=True)
projects_raw_data = group_data['projects']
project_names = list(map(lambda p: p['name'], projects_raw_data))
project_names_numbers = list(filter(None, map(lambda name: re.sub("[^0-9]", "", name), project_names)))
max_project_name = max(list(map(int, project_names_numbers))) if project_names_numbers else 0


#
# Read gitlab session cookie
#
print()
print("This script adds projects and get projects' info by interfacing with the git.uwaterloo.ca website directly.")
print("Please login to https://git.uwaterloo.ca and enter your _gitlab_session cookie from git.uwaterloo.ca below.")
gitlab_session_cookie = getpass.getpass("git.uwaterloo.ca _gitlab_session cookie value:")
print()


#
# Print and/or check the existing group memberships. Also checks that the input CSV file's
# data matches what already exists in git.uwaterloo.ca.
#
if print_current_membership or check_membership:
    # Hash that maps project names (Str) to a list of WatIAM ids.
    existing_memberships = {}
    print("Getting existing membership information from git.uwaterloo.ca...", flush=True)
    for project in projects_raw_data:
        if print_current_membership: print("  %s: "%project['name'], end='', flush=True)
        # Get members from API call. This doesn't return students who have been invited, but
        # haven't accepted their invitation yet.
        members_raw_data = gitlab.request("/projects/%d/members" % project['id'])
        members_list = list(map(lambda x : x['username'], members_raw_data))
        # Get members from the web page directly. 
        req = urllib.request.Request("https://git.uwaterloo.ca/%s/%s/project_members" % (group_name, project['name']),
                                     headers={'Cookie': "_gitlab_session=%s"%gitlab_session_cookie})
        with urllib.request.urlopen(req) as f:
            project_members_html = f.read().decode('utf-8')
            email_members = re.findall(r"([a-zA-Z0-9_.+-]+)@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", project_members_html)

        members_list = sorted(list(set(members_list + email_members)))
        if print_current_membership: print(', '.join(members_list), flush=True)
        existing_memberships[project['name']] = members_list

    # Also create a hash mapping student WatIAM ids to the groups they're in on gitlab [ String => listof(String) ]
    existing_memberships_by_userid = {}
    for repo_name, student_list in existing_memberships.items():
        for student in student_list:
            if student in existing_memberships_by_userid:
                existing_memberships_by_userid[student].append(repo_name)
            else:
                existing_memberships_by_userid[student] = [repo_name]

    # We've printed the current group memberships, so we can quit now.
    if print_current_membership:
        print("\nMemberships by WatIAM ID:")
        for userid in sorted(existing_memberships_by_userid.keys()):
            print("\t%s: %s" % (userid, ', '.join(existing_memberships_by_userid[userid])))
        sys.exit(0) # Done printing all group membership info

    # Check that each student is in only one group on gitlab
    for student, repo_names in existing_memberships_by_userid.items():
        if len(repo_names) >= 2:
            print("\nWARNING: Student %s is in multiple projects on git.uwaterloo.ca: %s" % (student, ', '.join(repo_names)))

    # Check that the CSV file has no duplicate IDs
    duplicates = find_duplicates(all_file_memberships)
    if duplicates:
        print("\nWARNING: These IDs occur multiple times in the CSV file %s: %s" % (membership_file, ', '.join(duplicates)))

    # Check that the groups in CSV file have 1-3 members. Also check that if the group
    # already exists in gitlab, check that the groups are exactly the same.
    for group_set in all_file_memberships:
        group = sorted(list(group_set))
        # Check group size is between 1-3
        if not group:
            print("\nWARNING: Found an empty group in %s. Ignoring it." % membership_file)
        elif len(group) > 3:
            print("\nWARNING: Found a group in %s with more than 3 members: %s" % (membership_file, ','.join(group)))
        # Check that if a student is in both the CSV file and a group on gitlab, the groups are exactly the same
        students_on_gitlab = list(filter(lambda s: s in existing_memberships_by_userid, group))
        if students_on_gitlab: # The CSV file has a student who's already in a group on gitlab
            groups_on_gitlab = existing_memberships_by_userid[students_on_gitlab[0]]
            if existing_memberships[groups_on_gitlab[0]] != group:
                print("\nWARNING: Student %s is in group %s {%s} on git.uwaterloo.ca, but CSV file %s has the student in group {%s}. Please check the members list on git.uwaterloo.ca and the CSV file. It's possible that people in the group just haven't accepted the invitation on git.uwaterloo.ca yet."
                      % (students_on_gitlab[0], groups_on_gitlab[0], ','.join(existing_memberships[groups_on_gitlab[0]]), membership_file, ','.join(group)))

    print("Finished checking. No errors above means no problems were found.") 
    sys.exit(0)



#
# Compute the new project names
#
projects_to_create = []
current_project_number = max_project_name + 1
for group in groups_to_create:
    name = 'group_' + '{:03}'.format(current_project_number)
    projects_to_create.append((name, group))
    current_project_number += 1

#
# Display the projects to be created and get a final confirmation before proceeding.
#
if not projects_to_create:
    print("No new projects to create. Quitting.")
    sys.exit(0)
print("The following %d projects will be created on git.uwaterloo.ca:\n" % len(projects_to_create))
for project_name, members in projects_to_create:
    print("  %s: %s" % (project_name, ', '.join(members)))
print()
print("NOTE: If you haven't already, it's recommended to first run this script with")
print("      --check-membership argument to make sure there aren't any problems")
print("      with the CSV file or the current membership assignments on git.uwaterloo.ca.")
print()
user_input = input("Create projects? (yes/no): ")
if user_input.lower() != "yes":
    print("Quitting.")
    sys.exit(0)


# Begin processing students
print("Creating %d new projects on git.uwaterloo.ca." % len(projects_to_create))
for project_name, members in projects_to_create:
    print(os.linesep)
    print('-' * 60)
    print("> Creating project %s with members: %s" % (project_name, ', '.join(members)))

    # Create project/repo for students who do not have one yet.
    if project_name in project_names:
        print("> Project %s already exists in group %s on git.uwaterloo.ca. Skipping it." % (project_name, group_name))
        continue

    # Project doesn't exist yet. Creating it.
    new_project = gitlab.request('projects', post_hash={'name':project_name, 'namespace_id':group_id, 'visibility_level':0})
    new_project_id = new_project['id']
    print("> Created new project %s with id %d" % (project_name, new_project_id))

    # Create master branch if it doesn't exist yet
    existing_branches = gitlab.request('projects/%d/repository/branches' % new_project_id)
    master_branch_exists = False
    for branch in existing_branches:
        if branch['name'] == 'master':
            master_branch_exists = True
    if not master_branch_exists:
        print("> master branch doesn't exist for %s. Creating it." % project_name)
        gitlab.request('projects/%d/repository/files' % new_project_id,
                       post_hash={'file_path':".gitignore", 'branch_name':"master", 'content':"#\n", 'commit_message':"Creating master branch"})
        time.sleep(1)

        # Wait for master branch to become protected. Gitlab seems to have a delay on protecting the
        # master branch when it's created.
        while True:
            master_branch_info = gitlab.request('/projects/%d/repository/branches/master' % new_project_id, quit_on_error=False)
            if master_branch_info and master_branch_info['protected']:
                print("> Newly created master branch has become protected.")
                break
            print("> Waiting for Gitlab to make newly created master branch protected.")
            time.sleep(1) # Don't spam Gitlab website
    else:
        print("> master branch already exists for %s. Not creating it." % project_name)


    # Turn off master branch protection (on by default). At this point
    # in the code, we have created master branch if it doesn't exist.
    # So master branch should exist. Also, if master is already unprotected,
    # then this operation does nothing (it's idempotent).
    print("> Unprotecting master branch.")
    gitlab.request('/projects/%d/repository/branches/master/unprotect' % new_project_id, http_method='PUT')
        
    # The project is now set up with an unprotected master branch. Add students to the project.
    print("> Adding student to project/repository.")

    # Step 1: Go to project_members web page and get authenticity token.
    print("> Getting authenticity token from project_members page.")
    authenticity_token = None
    req = urllib.request.Request("https://git.uwaterloo.ca/%s/%s/project_members" % (group_name, project_name),
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
        print("> Got authenticity token.")
        student_emails = ",".join(map(lambda userid: ldap.get_student_email(userid), members))
        print("> Adding members with emails: %s" % student_emails)
        post_data = urllib.parse.urlencode({'authenticity_token':authenticity_token,'user_ids':student_emails,'access_level':30}).encode('ascii')
        try:
            add_student_post = urllib.request.Request("https://git.uwaterloo.ca/%s/%s/project_members" % (group_name, project_name),
                                                      headers={'Cookie': "_gitlab_session=%s"%gitlab_session_cookie},
                                                      data=post_data, method='POST')
            urllib.request.urlopen(add_student_post)
        except Exception as e:
            sys.stderr.write("Error occured while adding %s to project %s. Perhaps the _gitlab_session cookie was entered wrong?\n" % (student_emails, project_name))
            sys.stderr.write(str(e) + "\n")
            sys.exit(1)
            
    else:
        print("> Could not get authenticity token to add students to project!")

    print("> Done processing project %s." % project_name)
    time.sleep(3) # Put in a bit of a delay so that git.uwaterloo.ca isn't hammered
