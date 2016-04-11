# Gitlab for Assignment Submission and Processing

This project has scripts to help courses use [UW's Gitlab](https://git.uwaterloo.ca) for
assignment submission and processing.

## How do courses use Gitlab?

Students will have a Git repo that they can use for revision control while doing their
assignment work. The typical setup is:

* A group is created for a course in a specific term. For example,
  the group might be called `cs123-spring2016`.
* In that group, there is a project/repo for each student. Students
  will be added as developers so that they can clone and push their
  work. By default, the master branch is protected, but this setting
  can be turned off. Adding students as developers ensures that they
  cannot change project settings like the name, which is vital for
  ensuring that you're marking the right work for the right student. 
  The script which automates the creation of repos, adding students as
  developers, and turning of master branch protection is `create-repos.py`.
* Course staff will be added to the group as owners. This lets course staff
  clone the students' repo for marking and distributing starter code. For marking,
  be sure to mark the correct revision (ie do not mark revisions made after the
  assignment deadline). Git's `rev-parse` and `rev-list` commands can help 
  with checking out the correct revision.
* A student's repo can be used for the entire term. Course staff can subdivide
  the repo by assignment. For example, the repo can have folders called `A1/`, 
  `A2/`, `A3/`, etc).
* When students are added to their repo as developers at the start of term, they will get an
  email informing them of that. 
* If students enroll late in the course, you can create repos for them using `create-repos.py`.
  Alternatively, you can create repos using the Gitlab web interface.

## Script Documentation

The scripts are written in [Python](https://www.python.org/). To run them, please have **Python
3.4 or higher** and **Git 1.8 or higher**. If you have any issues or questions about the scripts, please contact your course's
[CSCF Point of Contact](https://cs.uwaterloo.ca/cscf/teaching/contact/).

All scripts accept `-h` and `--help` arguments and will print a help message. More documentation is below.

### `clone.py`

The `clone.py` script is used to clone the students' repo. 
 
