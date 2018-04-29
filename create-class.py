#!/usr/bin/env python3
import gitlab
import simple_gitlab
import re
import argparse
import sys
import os

# This script is used to create a Gitlab group for a specified class and section. It can also use
# a classlist .CSV file to automatically add users that belong to that class and section to the 
# Gitlab group automatically.

# Pre-conditions: 
#   - The system has been properly installed
#   - Person using this script has admin access to the Gitlab server
#   - If a .csv file has been provided, it has the correct formatting (for formatting, see quick-start guide)

# Post-conditions:
#   - A Gitlab group has been created using the specified course number and section number
#   - Group name will be in 'course subject-course number-section number'
#   - If a .CSV file was used, all students from that course and section are added to the 
#   Gitlab group

gl = simple_gitlab.make_gitlab_obj(token_filename="test_token")

# Argument Parsing
parser = argparse.ArgumentParser(description="This script is used to create a Gitlab group for the specified class.")
parser.add_argument('--course-name', required=True, help="The course name (ex. CSCI125) of the desired course to create a Gitlab group for.")
parser.add_argument('--course-section',  required=True, help="The section of the course to create a Gitlab group for.")
parser.add_argument('--add-students', const=1, type=int, nargs='?', help="Use this if you wish to also add all students for this course to the Gitlab group.")
parser.add_argument('--file-name', nargs='?', help="The .CSV file from which you want to pull user data from.")

args = parser.parse_args()

# Set arguments as variables
class_name = args.course_name
class_section = args.course_section
add_students = args.add_students
file_name = args.file_name

class_name = class_name.lower()
subject = class_name[0:4]
course_number = class_name[4:7]

# Create string for the Gitlab group name based on arguments
gitlab_group_name = subject + "-" + course_number + "-" + class_section

# Add user to the group

# Pre-conditions:
#   - Gitlab group has been successfully created
#   - User_data is a line from the .CSV file where the course
#   name and section match the desired Gitlab group

# Post-conditions:
#   - User with credentials matching user_data is added to Gitlab group

def add_user_to_group(user_data):
    user_name = user_data[8][0:8]
    print("Adding " + user_name + " to " + gitlab_group_name + ".")
    user = gl.users.list(username=user_name)[0]
    group = gl.groups.get(gitlab_group_name)
    group.members.create({'user_id':user.id, 'access_level':gitlab.GUEST_ACCESS})

# Create a new Gitlab group using defined group name

# Pre-Conditions:
#   - A group name has been set

# Post-Conditions:
#   - A Gitlab group with the predefined group name is created 
def create_group():
    try:
        group = gl.groups.create({'name':gitlab_group_name, 'path':gitlab_group_name})
        print("Gitlab group created with name " + gitlab_group_name)
    except:
        print("Couldn't create Gitlab group for this class, group may already exist.")
        sys.exit()




file = None
students = []
if(add_students is not None):
    # --file-name flag not set
    if(file_name is None):
        print("File could not be found. Make sure you have used the '--file-name' flag correctly.")
        sys.exit()
    else:
        # Try to open the file for reading
        try: 
            file = open(file_name, 'r')
        except FileNotFoundError:
            print("File could not be found. Make sure file exists in this directory, and you have typed the name correctly.")
            sys.exit()

    # Search file for students    
    for line in file:
        user_data = re.split(',', line.rstrip())
        if (course_number == user_data[1] and class_section == user_data[2]):
            students.append(user_data)
    # If no students could be found in file with matching course number/section
    if(len(students) == 0):
        print("No students could be found for this class and section. Make sure the course number and section number are correct. GitLab group not created.")
    # If everything is OK, create new GitLab group and add all students from file
    else:
        create_group()
        for student in students:
            add_user_to_group(student)
    file.close()

if(add_students is None):
    create_group()



