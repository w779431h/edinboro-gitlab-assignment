#!/usr/bin/python3.4

import argparse
import sys,subprocess,os

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
