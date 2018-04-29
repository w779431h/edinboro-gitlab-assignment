Quickstart
==========

This is a quickstart guide to using the Edinboro Assignment Submission System

Prerequisites
-------------

You must have `git`, `python3.4`, and `pip3` installed. This guide assumes a Linux machine is used. In order to create students, you must be an administrator on the codestore instance. Talk to your system administrator for these priveleges if you are an instructor and you plan on creating users.

Installation
------------

To install the `python-gitlab` module, type:

`$ pip3 install python-gitlab`

In the directory that you would like your script to be installed, type:

`$ git clone https://github.com/GabrielDougherty/edinboro-gitlab-assignment.git`

`$ cd edinboro-gitlab-assignment`

Now, you can run any script by typing, `python3 scriptname.py`

Getting Help
------------

To see the available arguments for a command, simply type the command without arguments.

For example, typing `python3 create-class.py` lists the arguments for the `create-class` script.

Authentication
--------------

TODO

Creating User Accounts
----------------------

The first step to take in order to use scripts such as create-class.py, and create-group-projects.py, is to create any necessary user accounts. All of the students in your class must have a Gitlab account in order to participate in this system. This script gives the instructor (you) the ability to automatically create user accounts for all of the students in a certain course and section. If a student already has a user account, they will be skipped.

For this script to function, a roster .CSV file must be included in the same directory that this script is included in. The roster file should follow a format that matches the following:

`CSCI,408,1,SOFTWARE ENGINEERING,@00803819,Bob,Jim,5-Oct-97,jb123456@scots.edinboro.edu`  
`CSCI,408,1,SOFTWARE ENGINEERING,@00803819,Jackson,Bo,5-Oct-97,bj123456@scots.edinboro.edu`  
`CSCI,408,1,SOFTWARE ENGINEERING,@00803819,Woods,Tiger,5-Oct-97,tw123456@scots.edinboro.edu` 

Having multiple course and section numbers in the same file is fine, as the script will only create users that have a matching course and section number to what is defined by the professor (you). User accounts will be created using the following criteria:
* Email - Edinboro student email
* Username - Edinboro email address up until the '@'
* Password - Student's last name followed by the 6 digit number in their email address
* Name - First and last name

So, looking at a user with the following information:

`CSCI,408,1,SOFTWARE ENGINEERING,@00803819,Bob,Jim,5-Oct-97,jb123456@scots.edinboro.edu`  

We would get a user account with the following attributes:
* Email - jb123456@scots.edinboro.edu
* Username - jb123456
* Password - Bob123456
* Name- Jim Bob

To use this script, and add all of the students in the roster file that are members of CSCI408-1 from the csci408.CSV roster file, type:

`​$ python3 create-users.py --file-name csci408.CSV --course-number 408 --course-section 1​`

If the wrong file name is entered, or there are no students that belong to that course and section number, an error will be displayed and you will have to try again.

Creating a class
----------------

In GitLab, a class (i.e., CSCI408), is a GitLab Group. This is simply a collection of repositories on the server.

Our script for creating such a group assumes that the course will be identified by a course name and sections number. Hence, the instructor (you) must only provide the course name (i.e., CSCI408), and its section number (i.e., 1) to create a class.

In order to create the above class, section 1 of CSCI408, called `CSCI-408-1`, type:

`​$ python3 create-class.py --course-name "CSCI408" --course-section "1"​`

This script can also use a roster .CSV file to automatically add user accounts to the Gitlab group being created. This file must be included in the same directory as this script is included in. In order to create the above class, and add students from a roster file, type:

`​$ python3 create-class.py --course-name "CSCI408" --course-section "1" --file-name "csci408.csv"​`

The .CSV file should follow a format that matches the following:

`CSCI,408,1,SOFTWARE ENGINEERING,@00803819,Bob,Jim,5-Oct-97,jb123456@scots.edinboro.edu`  
`CSCI,408,1,SOFTWARE ENGINEERING,@00803819,Jackson,Bo,5-Oct-97,bj123456@scots.edinboro.edu`  
`CSCI,408,1,SOFTWARE ENGINEERING,@00803819,Woods,Tiger,5-Oct-97,tw123456@scots.edinboro.edu`  

If multiple classes/sections of a class are included in the classlist file, then only the students from the specified class and section number will be added from the file.
