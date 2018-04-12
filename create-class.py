#Creates a Gitlab group for the specified class
import gitlab
import simple_gitlab
import re
import argparse
from config import host_url, host_url_just_fqdn

gl = simple_gitlab.make_gitlab_obj(token_filename="test_token")

# Argument Parsing
parser = argparse.ArgumentParser(description="This script is used to create a Gitlab group for the specified class.")
parser.add_argument('--course_name', required=True, help="The course name (ex. CSCI125) of the desired course to create a Gitlab group for.")
parser.add_argument('--course_section',  required=True, help="The section of the course to create a Gitlab group for.")
parser.add_argument('--add_students', const=1, type=int, nargs='?', help="Use this if you wish to also add all students for this course to the Gitlab group.")
parser.add_argument('--file_name', nargs='?', help="The .CSV file from which you want to pull user data from.")

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

# Attempt to create a Gitlab group using the above group name
try:
    group = gl.groups.create({'name':gitlab_group_name, 'path':gitlab_group_name})
except:
    print("Couldn't create Gitlab group for this class, group may already exist.")

if(add_students==1):
    file = open(file_name, 'r')
    for line in file:
        user_data = re.split(',', line.rstrip())
        if (course_number == user_data[1] and class_section == user_data[2]):
            user_name = user_data[8][0:8]
            print("Adding " + user_name + " to the Gitlab group.")
            group = gl.groups.get(gitlab_group_name)
            group.members.create({'user_id':user_name, 'access_level':gitlab.GUEST_ACCESS})


