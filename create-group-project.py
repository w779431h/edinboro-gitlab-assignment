#!/usr/bin/env python3
#Creates a Gitlab group for the specified class
import gitlab
import simple_gitlab
import re
import argparse
import sys

gl = simple_gitlab.make_gitlab_obj(token_filename="test_token")

# Argument Parsing
parser = argparse.ArgumentParser(description="This script is used to create group projects within a specified Gitlab group.")
parser.add_argument('--group-name', required=True, help="The Gitlab group name (ex. csci-408-1) that you wish to create group projects in.")
parser.add_argument('--project-name', required=True, help="The name of the project you wish to create.")
parser.add_argument('--file-name', required=True, help="The .CSV file from which you want to pull group member info from.")


args = parser.parse_args()

# Set arguments as variables
group_name = args.group_name
project_name = args.project_name
file_name = args.file_name

group = None
group_id = None
try:
    group = simple_gitlab.get_group_by_name(gl, group_name)
    group_id = group.id
except:
    print("Gitlab group could not be found. Make sure it exists and you typed its name in correctly.")
    sys.exit()


# Try to open the file for reading
file = None
try: 
    file = open(file_name, 'r')
except FileNotFoundError:
    print("File " + file_name + " could not be found. Make sure file exists in this directory, and you have typed the name correctly.")
    sys.exit()


# Read the file, for each line create a new project and add all 
# users from that line to the project.
i = 1
for line in file:
    try:
        project = gl.projects.create({'name':project_name + " " + str(i), 
                                    'namespace_id':group_id})
    except:
        print("Unable to create group project, project name may already be in use.")
        sys.exit()
    usernames = re.split(',', line.rstrip())
    for name in usernames:
        user = gl.users.list(username=name)[0]
        project.members.create({'user_id': user.id, 'access_level': gitlab.DEVELOPER_ACCESS})
        print("Adding: " + name + " to " + project_name + " " + str(i) + ".")
    i = i + 1

file.close()
