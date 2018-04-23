import gitlab
import simple_gitlab
import re
import argparse
from config import host_url, host_url_just_fqdn

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
#users = gl.users.list()
#for user in gl.users.list():
    #print(user)

#print(courseData)


