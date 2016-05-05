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

group_to_clone_data = gitlab.request("groups/%d" % group_id)
projects_data = group_to_clone_data['projects']
all_usernames = []
urls = []
for project in projects_data:
    #print(project[
    #print(gitlab.request("projects/%s/members" % project['id']))
    #continue
    http_url = project['http_url_to_repo'] 
    #if gitlab_username:
    #    # User (TA or instructor) gave their Gitlab username
    #    # add it to http url
    #    http_url = re.sub('^https://git.uwaterloo.ca', "https://%s@git.uwaterloo.ca" % gitlab_username, http_url)
    ssh_url = project['ssh_url_to_repo']
    username = url2reponame(ssh_url)
    all_usernames.append(username)
    if (type(students) is not list) or (username in students):
        urls.append({'username': username,
                     'project_id': project['id'],
                     'http_url': http_url,
                     'ssh_url': ssh_url})
    members = gitlab.request("projects/%s/members" % project['id'])
    if len(members) >= 1:
        print("%s,%s,%s,%s" % (username,ssh_url,http_url,"accepted"))
    else:
        print("%s,%s,%s,%s" % (username,ssh_url,http_url,"DID NOT ACCEPT INVITE YET"))
