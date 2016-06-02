#!/usr/bin/ssh-agent /usr/bin/python3

import gitlab
import pprint # useful for debugging
import argparse,getpass,re,time
from datetime import datetime
import sys,subprocess,os
import json,urllib.request

#
# Helper functions
#

# Checks if s contains a valid date and time format. If it is
# valid, return it as a datetime object. Otherwise, raises an
# error.
def valid_datetime(s):
    date_formats = [(s, '%Y-%m-%d %H:%M:%S%z'),
                    (s + time.strftime('%z'), "%Y-%m-%d %H:%M:%S%z"),
                    (s, '%Y-%m-%d %H:%M%z'),
                    (s + time.strftime('%z'), '%Y-%m-%d %H:%M%z')]
    for datetime_str, date_format in date_formats:
        try:
            return datetime.strptime(datetime_str, date_format)
        except ValueError:
            pass
    raise argparse.ArgumentTypeError("Could not parse %s." % s)

# Given a http or ssh git URL, return the repository name
# Example:
# url2reponame('gitlab@git.uwaterloo.ca:cs349-test1/johnsmith.git')
# => 'johnsmith'
def url2reponame(url):
    return url.rsplit('/',1)[-1][:-4]


#
# Parse command-line arguments.
# Inputs are stored in group_to_clone, url_type, token_file
# clone_dir, revert_date
#

parser = argparse.ArgumentParser(description="This script is used to clone student repositories.")
parser.add_argument('group_name', help="The name of the Gitlab group whose projects you want to clone.")
parser.add_argument('--url-type', choices=['http','ssh','http-save','ssh-save'], default='http',
                    help="Git URL to use (http or ssh). If the -save versions are used, your password will be saved in memory so that " +
                         "you only have to type your password once. Default is http.")
parser.add_argument('--token-file', default="/dev/stdin",
                    help="Path to file containing your Gitlab private token. Default is to read from standard input.")
parser.add_argument('--clone-dir', help="Directory to clone repositories to. Default is; ./group_name/")
parser.add_argument('--revert-date', type=valid_datetime, help="Once cloned, revert repos to this date on master branch. " + 
                    "Format: 'YYYY-MM-DD hh:mm[:ss][-TTTT]' where TTTT is timezone offset, ex -0400.")
parser.add_argument('--students', help="A comma separated list of student Quest IDs.  If given, only these student's repos will be cloned. " +
                                       "Default is to clone every project in the group.")
parser.add_argument('--username', help="Username on git.uwaterloo.ca (same as Quest ID).")
args = parser.parse_args()

# save command line argument inputs in variables
group_to_clone = args.group_name
url_type = args.url_type
token_file = args.token_file
clone_dir = args.clone_dir if args.clone_dir else ("./"+group_to_clone+"/")
revert_date = args.revert_date
gitlab_username = args.username
if args.students:
    students = list(map(lambda s:s.strip(), args.students.split(',')))
    students = list(filter(lambda s: s and not s.isspace(), students))
else:
    students = None

# Read private token from keyboard or from file
gitlab.set_private_token(token_file)

# for debugging
# print("group_to_clone=%s" % group_to_clone)
# print("url_type=%s" % url_type)
# print("token_file=%s" % token_file)
# print("clone_dir=%s" % clone_dir)
# print("revert_date=%s" % str(revert_date))
# print("students=%s" % str(students))


#
# Get the ID of group_to_clone
# ID will be stored in group_id
#

print("Getting ID of group %s." % group_to_clone)
group_id = gitlab.get_group_id(group_to_clone)
print("Found group %s which has ID %d" % (group_to_clone, group_id))


#
# Get URL of the projects in the group that will be cloned.
# urls will be list of hashes, each hash containing the keys:
#   username: A string, the student username
#   project_id: An integer, the project id
#   http_url: A string, the repo http url
#   ssh_url: A string, the repo ssh url
#

print("Getting git repo URLs in group %s (id %d)." % (group_to_clone, group_id))

group_to_clone_data = gitlab.request("groups/%d?per_page=10000" % group_id)
projects_data = group_to_clone_data['projects']
all_usernames = []
urls = []
for project in projects_data:
    http_url = project['http_url_to_repo'] 
    if gitlab_username:
        # User (TA or instructor) gave their Gitlab username
        # add it to http url
        http_url = re.sub('^https://git.uwaterloo.ca', "https://%s@git.uwaterloo.ca" % gitlab_username, http_url)
    ssh_url = project['ssh_url_to_repo']
    username = url2reponame(ssh_url)
    all_usernames.append(username)
    if (type(students) is not list) or (username in students):
        urls.append({'username': username,
                     'project_id': project['id'],
                     'http_url': http_url,
                     'ssh_url': ssh_url})
urls.sort(key = lambda proj: proj['username'])

# If the user uses --students command line option and gives an invalid
# username, find it and report
problematic_usernames = []
if type(students) is list:
    for username in students:
        if username not in all_usernames:
            print("WARNING: Cannot find URL for student %s in group %s." % (username, group_to_clone))
            problematic_usernames.append(username)


#
# Clone the repositories.
#

# Create folder where the repos will be cloned to
os.makedirs(clone_dir, mode=0o700, exist_ok=True)
os.chdir(clone_dir)

# If the user wants to save authentication information, do that now
if url_type == 'http-save':
    cmd = ['git', 'config', '--global', 'credential.helper', 'cache']
    print("Using git credential helper to save your password.")
    print("Running command: " + ' '.join(cmd))
    subprocess.call(cmd)
elif url_type == 'ssh-save':
    print("Running ssh-agent and ssh-add to save SSH passphrase.")
    subprocess.call('ssh-agent')
    subprocess.call('ssh-add')

# Loop over each student and clone
students_without_revision = []
print("Cloning projects to the folder %s." % clone_dir)
if revert_date:
    print("Also checking out latest commit from latest push before %s." % revert_date)
for url_info in urls:
    # Get the right type of url to use (http or ssh)
    if url_type == 'http' or url_type == 'http-save':
        url = url_info['http_url']
    elif url_type == 'ssh' or url_type == 'ssh-save':
        url = url_info['ssh_url']

    username = url2reponame(url)

    print(os.linesep)
    print('-' * 60)
    if os.path.isdir(username) and os.listdir(username):
        print("> Destination folder %s already exists and is not empty." % username)
        print("> Not cloning %s." % url)
    else:
        print("> Cloning " + url)
        subprocess.call(['git', 'clone', url])

    # Checkout the latest commit from the latest push that was made before
    # the given date.
    if revert_date:
        # Find the latest push that's on or before revert_date
        ontime_push_time = None
        ontime_commit    = None
        project_events = gitlab.request('projects/%s/events?per_page=10000000' % url_info['project_id'])
        for event in project_events:
            # Only care about project events that are pushes to master branch
            if event['action_name'] in ['pushed to', 'pushed new'] and event['data']['ref'] == 'refs/heads/master':
                # Gitlab has time in a format not easily read by Python's datetime,
                # so do a little formatting with regex.
                created_at_py = re.sub('([\d]{2})\.[\d]{3}(.[\d]{2}):([\d]{2})', r"\1\2\3", event['created_at'])
                created_at = datetime.strptime(created_at_py, "%Y-%m-%dT%H:%M:%S%z")
                if created_at <= revert_date and (not ontime_push_time or created_at > ontime_push_time):
                    ontime_push_time = created_at
                    ontime_commit = event['data']['after']
        if ontime_push_time:
            print("> Using commit %s from the push dated %s." % (ontime_commit, ontime_push_time))
            print("> Checking out commit %s." % ontime_commit)
            if os.path.isdir(username):
                os.chdir(username)
                try:
                    subprocess.call(['git', 'checkout', ontime_commit])
                except Exception as e:
                    print("> git checkout failed!")
                    students_without_revision.append(username)
                os.chdir(os.pardir)
            else:
                print("> Directory %s doesn't exist. Cannot run git checkout." % username)
                students_without_revision.append(username)
        else:
            print("> Could not find any pushes to master branch before %s." % revert_date)
            students_without_revision.append(username)

# Erase saved http credentials
if url_type == 'http-save':
    print(os.linesep)
    print("Done cloning. Erasing saved http credentials.")
    subprocess.call(['git', 'config', '--global', '--unset-all', 'credential.helper'])

if problematic_usernames:
    print(os.linesep)
    print('-' * 60)
    print("Could not find git repo URL for students:")
    print(' '.join(problematic_usernames))
    print("No actions were performed for the above students.")

if revert_date and students_without_revision:
    print(os.linesep)
    print('-' * 60)
    print("Could not checkout a revision before %s for these students:" % revert_date)
    print(' '.join(students_without_revision))
