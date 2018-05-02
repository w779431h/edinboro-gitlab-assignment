#!/usr/bin/env python3

import argparse
import sys,subprocess,os

# This script is used to run a command-line program in every folder in a
# given folder. This script takes a command and target parent directory for the
# command to be run in. Generally, this would be used to run a command inside
# every student folder in a cloned class (GitLab Group).

# Pre-conditions:
#   - The system has been properly installed
#   - Person using this script has a folder two levels deep, such as a downloaded
#     GitLab Group

# Post-conditions:
#   - The given command has been executed in every directory inside the given
#     parent directory
#   - Information on the command and directories have been printed to the screen


parser = argparse.ArgumentParser(description="Runs a command or program in every folder in a given folder.")
parser.add_argument("parent_dir", help="The given command will be run on each folder X inside parent_dir.")
parser.add_argument("command", help="Command or path to program to run inside X.")
parser.add_argument("--pass-name", action='store_true', help="If specified, the directory name X will be passed to the command as an argument.")
parser.add_argument("--headers", action='store_true', help="Prints a header containing X before running the command.")
args = parser.parse_args()

parent_dir = args.parent_dir
command = args.command
pass_name = args.pass_name
headers = args.headers

# for debugging
# print("parent_dir=" + str(parent_dir))
# print("command=" + str(command))
# print("pass_name=" + str(pass_name))

# Navigate into parent_dir
try:
    os.chdir(parent_dir)
except Exception as e:
    print("Could not navigate to directory %s" % parent_dir)
    print("Error message: %s" % str(e))
    sys.exit(1)

# Loop over each directory in parent_dir (where we're at now)
looped_once = False
for item in os.listdir(os.getcwd()):
    # Skip files
    if not os.path.isdir(item):
        continue

    os.chdir(item)
    if headers:
        if looped_once:
            print()
        print(">>> Running command in %s" % os.path.abspath(item))

    # Execute given command
    if pass_name:
        subprocess.call(command + " " + item, shell=True)
    else:
        subprocess.call(command, shell=True)
    os.chdir(os.pardir)
    looped_once = True
