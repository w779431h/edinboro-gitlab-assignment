#!/usr/bin/env python3
import simple_gitlab
import re
import argparse

# This script is used alongside a classlist .csv file to create Gitlab user accounts for
# all students in a certain class and section.

# Pre-conditions: 
#   - The system has been properly installed
#   - Person using this script has admin access to the Gitlab server
#   - A .csv file has been provided with the correct formatting (for formatting, see quick-start guide)

# Post-conditions:
#   - User accounts for all students in the specified course/section should be created
#   - Each account uses the first 8 characters in the student email as a username
#   - Each account uses the last name + the 6 digit number in Edinboro email as a password


gl = simple_gitlab.make_gitlab_obj(token_filename="test_token")

# Argument Parsing
parser = argparse.ArgumentParser(description="This script is used to create any user accounts that do not yet exist from a classlist.")
parser.add_argument('--file-name',  required=True, help="The .CSV file from which you want to pull user data from.")
parser.add_argument('--course-number',  required=True, help="The course number (ex. 125) of the desired course to add users from.")
parser.add_argument('--course-section',  required=True, help="The section of the course to add users from.")
args = parser.parse_args()

#Set arguments as variables
file_name = args.file_name
class_name = args.course_number
class_section = args.course_section

# Pulls user information from the file

# Pre-conditions:
#   - .CSV file has been properly defined and is opened for reading

# Post-conditions:
#   - User account is created using the information passed to the funciton by users argument

# Email = Edinboro email
# Username = Edinboro email address up to the @
# Password = Lastname (with capital first letter) + 6 digit number in Edinboro email
# Name = First and last name
def createUser(user):
    email = user[8]
    username = user[8][0:8]
    password = user[5] + user[8][2:8]
    name = user[6] + " " + user[5]
    try:  
        # Create user account using data from file
        createUser = gl.users.create({'email': email,
                                'password': password,
                                'username': username,
                                'name': name})
    except:
        print("Couldn't create student account, account may already exist.")
                            



# Parse file, find any entries that match the above input
# and send entries to the create user function
found = False
try: 
    file = open(file_name, 'r')
    for line in file:
        user_data = re.split(',', line.rstrip())
        if (class_name == user_data[1] and class_section == user_data[2]):
            print("Adding: " + user_data[6] + " " + user_data[5])
            found = True
            createUser(user_data)
    file.close()
except FileNotFoundError:
    print("File could not be found. Make sure file exists in this directory, and you have typed the name correctly.")

if(found == False):
    print("No students could be found for this class and section. Make sure the course number and section number are correct.")



