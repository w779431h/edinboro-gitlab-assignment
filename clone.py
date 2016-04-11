#!/usr/bin/ssh-agent /usr/bin/python3

import pprint # useful for debugging
import argparse,datetime,getpass
import sys,subprocess,os
import json,urllib.request

#
# Helper functions
#

# gitlab_query makes a request to https://git.uwaterloo.ca/api/v3/
# and returns the JSON data as a Python object
# Input: query: Part of URL after the URL above
# Returns: A python object
def gitlab_query(query):
    try:
        req = urllib.request.Request(url="https://git.uwaterloo.ca/api/v3/" + query,\
                                     headers={'PRIVATE-TOKEN': private_token})
        with urllib.request.urlopen(req) as f:
            json_string = f.read().decode('utf-8')
            try:
                python_object = json.loads(json_string)
            except Exception as e:
                print(json_string)
                print("Error occurred trying to interpret above data as JSON.")
                print("Error message: %s" % str(e))
                sys.exit(1)
            return python_object
    except Exception as e:
        print("Error occurred trying to access https://git.uwaterloo.ca/api/v3/" + query)
        print("Error message: %s" % str(e))
        sys.exit(1)

# Checks if s contains a valid date and time format. If it is
# valid, return it as a datetime object. Otherwise, raises an
# error.
def valid_datetime(s):
    try:
        return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        msg = "Not a valid date time: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)

# Given a http or ssh git URL, return the repository name
# Example:
# url2reponame('gitlab@git.uwaterloo.ca:cs349-test1/johnsmith.git')
# => 'johnsmith'
def url2reponame(url):
    return url.rsplit('/',1)[-1][:-4]


#
# Parse command-line arguments.
# Inputs are stored in group_to_clone, url_type, token_file
# clone_dir, revert_to_date
#

parser = argparse.ArgumentParser(description="This script is used to clone student repositories.")
parser.add_argument('group_name', help="The name of the Gitlab group whose projects you want to clone.")
parser.add_argument('--url-type', choices=['http','ssh','http-save','ssh-save'], default='http',
                    help="Git URL to use (http or ssh). If the -save versions are used, your password will be saved in memory so that " +
                         "you only have to type your password once. Default is http.")
parser.add_argument('--token-file', default="/dev/stdin",
                    help="Path to file containing your Gitlab private token. Default is to read from standard input.")
parser.add_argument('--clone-dir', help="Directory to clone repositories to. Default is; ./group_name/")
parser.add_argument('--revert-to-date', type=valid_datetime, help="Once cloned, revert repos to this date on master branch. Format: 'YYYY-MM-DD hh:mm:ss'")
parser.add_argument('--students', help="A comma separated list of student Quest IDs.  If given, only these student's repos will be cloned. " +
                                       "Default is to clone every project in the group.")
args = parser.parse_args()

# save command line argument inputs in variables
group_to_clone = args.group_name
url_type = args.url_type
token_file = args.token_file
clone_dir = args.clone_dir if args.clone_dir else ("./"+group_to_clone+"/")
revert_to_date = args.revert_to_date
if args.students:
    students = list(map(lambda s:s.strip(), args.students.split(',')))
    students = list(filter(lambda s: s and not s.isspace(), students))
else:
    students = None

# Read private token from keyboard or from file
if token_file == "/dev/stdin":
    print("You can get your Gitlab private token from https://git.uwaterloo.ca/profile/account")
    private_token = getpass.getpass("Please enter your Gitlab private token:")
else:
    try:
        token_file_handle = open(token_file, 'r')
        private_token = token_file_handle.readline().strip()
        token_file_handle.close
    except Exception as e:
        print("Error occurred trying to read private token from file %s" % token_file)
        print("Error message: %s" % str(e))
        sys.exit(1)

# for debugging
# print("group_to_clone=%s" % group_to_clone)
# print("url_type=%s" % url_type)
# print("token_file=%s" % token_file)
# print("clone_dir=%s" % clone_dir)
# print("revert_to_date=%s" % str(revert_to_date))
# print("students=%s" % str(students))


#
# Get the ID of group_to_clone
# ID will be stored in group_id
#

print("Getting ID of group %s." % group_to_clone)

group_id = None
groups_data = gitlab_query("groups")
for group in groups_data:
    if group['name'] == group_to_clone:
        group_id = group['id']
        break
if group_id == None:
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

print("Found group %s which has ID %d" % (group_to_clone, group_id))


#
# Get URL of the projects in the group that will be cloned.
# urls will be list of urls to clone
#

print("Getting URLs in group %s (id %d)." % (group_to_clone, group_id))

group_to_clone_data = gitlab_query("groups/%d" % group_id)
projects_data = group_to_clone_data['projects']
all_usernames = []
urls = []
for project in projects_data:
    http_url = project['http_url_to_repo'] 
    ssh_url = project['ssh_url_to_repo']
    username = url2reponame(ssh_url)
    all_usernames.append(username)
    if (type(students) is not list) or (username in students):
        if url_type == 'http' or url_type == 'http-save':
            urls.append(http_url)
        elif url_type == 'ssh' or url_type == 'ssh-save':
            urls.append(ssh_url)
urls.sort()

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
    cmd = ['git', 'config', '--global', 'credential.helper', "'cache --timeout=1800'"]
    print("Using git credential helper to save your password.")
    print("Running %s" % ' '.join(cmd))
    subprocess.call(cmd)
elif url_type == 'ssh-save':
    print("Running ssh-agent and ssh-add to save SSH passphrase.")
    subprocess.call('ssh-agent')
    subprocess.call('ssh-add')

# Loop over each student and clone
students_without_revision = []
print("Cloning projects to the folder %s." % clone_dir)
for url in urls:
    print(os.linesep)
    print('-' * 60)
    print("> Cloning " + url)
    subprocess.call(['git', 'clone', url])
    if revert_to_date:
        username = url2reponame(url)
        os.chdir(username)
        print("> Reverting master branch to date %s in folder %s." % (revert_to_date, os.path.abspath(os.curdir)))
        try:
            # First grab the student's latest work on master branch
            retcode1 = subprocess.call('git checkout master'.split())
            retcode2 = subprocess.call('git pull origin master'.split())
            if retcode1 != 0 or retcode2 != 0:
                print("> Cannot checkout and pull from master branch!")
                raise
            # Then checkout the last revision before due date
            revision_to_use = subprocess.check_output(['git', 'rev-list', '-n1', '--before="%s"'%revert_to_date, '--first-parent', 'master']).strip()
            if revision_to_use:
                print("> Checking out revision %s" % revision_to_use)
                subprocess.call(['git', 'checkout', revision_to_use])
            else:
                print("> Cannot find a revision before %s" % revert_to_date)
                raise
        except Exception as e:
            print("> Could not revert %s! A revision might not exist before %s in master branch." % (username, revert_to_date))
            students_without_revision.append(username)
        os.chdir(os.pardir)

if problematic_usernames:
    print(os.linesep)
    print('-' * 60)
    print("Could not find URL for students:")
    print(' '.join(problematic_usernames))
    print("No actions were performed for the above students.")

if revert_to_date and students_without_revision:
    print(os.linesep)
    print('-' * 60)
    print("Could not checkout a revision before %s for these students:" % revert_to_date)
    print(' '.join(students_without_revision))
