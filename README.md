# Gitlab for Assignment Submission and Processing

This project has scripts to help courses use [UW's Gitlab](https://git.uwaterloo.ca) for
assignment submission and processing.

## How do courses use Gitlab?

Students will have a Git repo that they can use for revision control while doing their
assignment work. The setup is:

* A Gitlab group is created for a course for a specific term. For example,
  the group might be called "cs123-spring2016".
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
  assignment deadline).
* A student's repo can be used for the entire term. Course staff can subdivide
  the repo by assignment. For example, the repo can have folders called `A1/`, 
  `A2/`, `A3/`, etc).
* Students will get an invitation email when they're added to their repo as
  a developer at the start of term. Students who have never used git.uwaterloo.ca before
  must click the link in the email.
* If students enroll late in the course, you can create repos for them using `create-repos.py`.
  Alternatively, you can create repos manually using git.uwaterloo.ca web interface.

## Caveats

* You should not trust commit dates. They can be faked intentionally (ex. the student tries to 
  pass off late work as being on time) or unintentionally (ex. the clock on the student's
  computer is wrong). However, the times associated with push events can be trusted because those times
  come from the Gitlab server when the student pushes. The scripts use push times, not commit times.
* Students **must** push their work to the master branch before the assignment due date. If students commit
  on time, but forgets to push until after the due date, their work is considered late.
* When students clone their repo with http url, they might get the error `fatal: repository 'https://git.uwaterloo.ca/...' not found`.
  Fix this by using the url `https://<questID>@git.uwaterloo.ca/...` instead (add Quest ID to url).
* Students should have their @uwaterloo.ca email set up correctly at the start of term. Gitlab sends
  invitation emails from hub.uwaterloo.ca. Student should not block this domain or filter out or block
  Gitlab emails.

## Script Documentation

The scripts are written in [Python](https://www.python.org/). To run them, please have **Python
3.4 or higher** and **Git 1.8 or higher**. If you have any issues or questions about the scripts, please contact your course's
[CSCF Point of Contact](https://cs.uwaterloo.ca/cscf/teaching/contact/).

You can save the output of the scripts (or any command line program really) using [tee](https://en.wikipedia.org/wiki/Tee_%28command%29).
For example, you can run `python3 clone.py cs123-spring2016 | tee clone-ouput.txt`.

All scripts accept `-h` and `--help` arguments and will print a help message. You may have to make the scripts
executable before running them (for example, with `chmod 700`). More documentation is below.

### `clone.py`

The `clone.py` script is used to clone the students' repositories and to checkout the last
commit in the last push to master branch before a certain time.

#### Arguments:

* `group_name`: The only mandatory argument is the group name. The group name can be found from the
  Gitlab [Groups page](https://git.uwaterloo.ca/dashboard/groups). Course staff, including TAs, should
  be added to the group as owners using the web interface.
* `--url-type {http,ssh,http-save,ssh-save}`: You can choose to use either `http` or `ssh` for the repository
  URL. The default is `http`. To setup `ssh`, see the Gitlab doc on [SSH keys](https://git.uwaterloo.ca/help/ssh/README).
  If you are cloning many repositories, typing in your credentials every time is exhausting. You can make `clone.py` remember
  your credentials using the `-save` versions. For `http-save`, your credentials is saved for 15 minutes in memory with
  the command:
  
  `git config --global credential.helper cache`

  You can clear the cached credentials with: `git config --global --unset-all credential.helper`.
  For `ssh-save`, your passphrase is saved using `ssh-agent` and `ssh-add`.
* `--token-file TOKEN_FILE`: Access to Gitlab is needed to get all the projects in the group. You can
  find your private token from Gitlab [Account page](https://git.uwaterloo.ca/profile/account). By default, you'll
  be asked to type it in (won't be echo'ed back). If you don't want to keep typing in the token, save the token in
  the first line of a file by itself, then set `TOKEN_FILE` to a path to the file.
* `--clone-dir CLONE_DIR`: Will clone the students' repositories into the folder `CLONE_DIR`. The default is `./group_name/`,
  ie a folder with the same name as `group_name` in the current directory.
* `--revert-date REVERT_TO_DATE`: This option will checkout the last commit in the last push to the master branch
  before `REVERT_TO_DATE`, which can be in one of these formats:

   * 2016-05-30 15:10 (will use 00 seconds and current timezone on the computer running the script)
   * 2016-05-30 15:10-0400
   * 2016-05-30 15:10:30
   * 2016-05-30 15:10:30-0400

  If a timezone isn't given, the current timezone on the system will be used.
  If the `--revert-date` option isn't given, the script will just clone.
* `--students STUDENTS`: The default is to clone (and possibly revert) all the repositories in the given group. Use this option if you only want to 
  perform these actions on a select set of students. `STUDENTS` should be a comma separated list of student Quest IDs.
* `--username USERNAME`: On some systems, you need to include your Gitlab username in the url or you'll get a "repository not found" error.
  If you get that error, pass in your Gitlab username (same as your Quest ID) with this option.
  
#### Examples:

1. `python3 clone.py cs123-spring2016 --url-type http-save`

    Clones all the repositories in the group cs123-spring2016 to the folder `./cs123-spring2016`.
    You'll be asked to type in your private token and your Gitlab credentials once. The only git
    command that will be run is `git clone`. You might run this near the start of term to clone
    all the students' repos.

1. `python3 clone.py cs123-spring2016 --token-file ~/.gitlab_token --url-type http-save`

    Same as above, except that the private token will be read from the first line of ~/.gitlab_token, a
    text file you have to create manually.

1. `python3 clone.py cs123-spring2016 --url-type ssh-save --revert-date '2016-05-30 13:00:00' --students j4ansmith,yralimonl,t2yang`

    Clones the repositories for three students j4ansmith, yralimonl, and t2yang. Then checkout the last commit in the last push made 
    to the master branch before 1:00pm on May 30, 2016.

### `batch-operation.py`

Runs a command or program in every folder in a given folder.

#### Arguments:

* `parent_dir`: Mandatory. The command will be run inside each folder in `parent_dir`.
* `command`: Mandatory. The command to run inside the folders in `parent_dir`. If you need
  to pass arguments to the command, put the command and all its arguments in quotes.
* `--headers`: If specified, a header will be printed before each running of the command.
* `--pass-name`: If specified, the folder names in `parent_dir` will be passed to `command`.

#### Examples:

1. This example runs the [`pwd`](https://en.wikipedia.org/wiki/Pwd) command inside each folder in cs349-test1.

        $ ls cs349-test1/
        cscf-t01  cscf-t02  cscf-t03  cscf-t04  cscf-t05  random-project
        $ python3 batch-operation.py cs349-test1/ pwd
        /u5/yc2lee/gitlab-assignments/cs349-test1/cscf-t01
        /u5/yc2lee/gitlab-assignments/cs349-test1/cscf-t02
        /u5/yc2lee/gitlab-assignments/cs349-test1/cscf-t03
        /u5/yc2lee/gitlab-assignments/cs349-test1/cscf-t04
        /u5/yc2lee/gitlab-assignments/cs349-test1/cscf-t05
        /u5/yc2lee/gitlab-assignments/cs349-test1/random-project
        $

1. This example will pass the folder name to `echo Hello,` and print an informative header.

        $ python3 batch-operation.py --headers --pass-name cs349-test1 'echo Hello,'
        >>> Running command in /u5/yc2lee/gitlab-assignments/cs349-test1/cscf-t01/cscf-t01
        Hello, cscf-t01
        
        >>> Running command in /u5/yc2lee/gitlab-assignments/cs349-test1/cscf-t02/cscf-t02
        Hello, cscf-t02
        
        >>> Running command in /u5/yc2lee/gitlab-assignments/cs349-test1/cscf-t03/cscf-t03
        Hello, cscf-t03
        
        >>> Running command in /u5/yc2lee/gitlab-assignments/cs349-test1/cscf-t04/cscf-t04
        Hello, cscf-t04
        
        >>> Running command in /u5/yc2lee/gitlab-assignments/cs349-test1/cscf-t05/cscf-t05
        Hello, cscf-t05
        
        >>> Running command in /u5/yc2lee/gitlab-assignments/cs349-test1/random-project/random-project
        Hello, random-project
        $

1. After you clone all the students' repositories with `clone.py`, you can run custom commands on all
   the repos with `batch-operation.py`. There are four fatal errors because those repositories are empty
   and have no commits to show.

        $ python3 batch-operation.py --headers cs349-test1/ 'git log -1 --oneline'
        >>> Running command in /u5/yc2lee/gitlab-assignments/cs349-test1/cscf-t01/cscf-t01
        adb4691 nick testing push
        
        >>> Running command in /u5/yc2lee/gitlab-assignments/cs349-test1/cscf-t02/cscf-t02
        fatal: bad default revision 'HEAD'
        
        >>> Running command in /u5/yc2lee/gitlab-assignments/cs349-test1/cscf-t03/cscf-t03
        fatal: bad default revision 'HEAD'
        
        >>> Running command in /u5/yc2lee/gitlab-assignments/cs349-test1/cscf-t04/cscf-t04
        fatal: bad default revision 'HEAD'
        
        >>> Running command in /u5/yc2lee/gitlab-assignments/cs349-test1/cscf-t05/cscf-t05
        fatal: bad default revision 'HEAD'
        
        >>> Running command in /u5/yc2lee/gitlab-assignments/cs349-test1/random-project/random-project
        3fd99a6 another test
        $

### `create-repos.py`

The `create-repos.py` script sets up repositories for a set of students. It should be
run once at the start of term. This script will, for each student:

1. Create a project/repository if one doesn't exist yet.
1. Commit a `.gitignore` to the master branch. The `.gitignore` file has one line, which is just a `#`.
1. Unprotect the master branch. Gitlab makes master branches protected by default.
1. If the `--add-students` option is given, add student as developers. This action will send an invitation
   email to the student's @uwaterloo.ca email address.

#### Arguments:

* `group_name`: The only mandatory argument is the group name. The students' repositories will be
  added to this group, which should be created manually from the Gitlab [Groups page](https://git.uwaterloo.ca/dashboard/groups)
  before running this script.
* `--token-file TOKEN_FILE`: Same usage as in `clone.py`.
* `--add-students`: Pass this option if you want to add students. By default, students will not be added. If you set this option,
                    the script will ask you for your `_gitlab_session` cookie which you can get by logging in to
                    https://git.uwaterloo.ca and searching for `_gitlab_session` cookie. It should be on the site git.uwaterloo.ca.
                    The `_gitlab_session` cookie is a hash (ex. `5bcgf155e6add457d75c20db6045r9e9`).
* `--classlist CLASSLIST`: Path to your course's `.classlist` file on the linux.student.cs.uwaterloo.ca servers. The full
                           path is `/u/csXXX/.classlist` where XXX is your course number. The `.classlist` file is updated
                           automatically each midnight using enrollment data from the registrar.
* `--students STUDENTS`: You can set up repositories of a specific list of students instead of the whole class.
                         `STUDENTS` should be a comma separated list of student Quest IDs. This option cannot be used
                         with `--classlist`.

#### Examples:

1. `./create-repos.py cs123-spring2015 --token-file ~/.gitlab_token --add-students --students j4ansmith,yralimonl,t2yang`

    Reads your private Gitlab token from the file `~/.gitlab_token`. Then sets up projects for j4ansmith, yralimonl, and t2yang
    in the group `cs123-spring2015`. Also adds the three students to their project. Gitlab will send an invitation email
    to their @uwaterloo.ca email address.

1. `./create-repos.py cs123-spring2015 --add-students --classlist /u/cs123/.classlist`

    Sets up projects for all students in `/u/cs123/.classlist` at the time the script is run. Also adds students to their
    project.

### `stqam-create-repos.py`

The `stqam-create-repos.py` is used for CS447/SE465/ECE453 "Software Testing, Quality Assurance and Maintenance" course. This script
creates projects for each student group according to an input CSV file, and adds the students to the group as developers.

When running the script, you will be prompted for you `_gitlab_session` cookie. The script uses the cookie to interface with the Gitlab
web page directly when there's no appropriate API calls available. Most browsers can show you the cookie value in the privacy settings.
The script will not print what you type for security.

        $ ./stqam-create-repos.py --help
        usage: stqam-create-repos.py [-h] [--token-file TOKEN_FILE]
                                     [--current-membership] [--check-membership]
                                     group_name membership_file
        
        This script is used to create student repositories for cs447/ece453/se465.
        
        positional arguments:
          group_name            The name of the Gitlab group to create projects in.
          membership_file       Path to a CSV containing group memberships, with
                                fields: Timestamp, WatIAM user id for member 1, WatIAM
                                user id for member 2 (optional), WatIAM user id for
                                member 3 (optional), Group number (optional)
        
        optional arguments:
          -h, --help            show this help message and exit
          --token-file TOKEN_FILE
                                Path to file containing your Gitlab private token.
                                Default is to read from standard input.
          --current-membership  Prints the current group memberships according to
                                git.uwaterloo.ca and quit.
          --check-membership    Checks the membership_file against the current group
                                memberships. Prints any problems it finds and quit.

#### Arguments:

* `group_name`: This mandatory argument is the group name for the course offering in Gitlab. For example, 'stqam-2017'. Someone should
   manually create the group from the Gitlab [Groups page](https://git.uwaterloo.ca/dashboard/groups) at the start of the term.
* `membership_file`: This mandatory argument is the path to a CSV file containing information about student groups. The first line of the CSV file
   is a header line and is ignored. Subsequent lines should contain these fields in order:
   * Timestamp. Example: 2/10/2017 14:27:21
   * Userid 1. Example: j29smith
   * Userid 2. Can leave blank.
   * Userid 3. Can leave blank.
   * The last field is a number or blank. If there's a number, the script will not create the project. If it's blank, the project will be created.
     The number can be arbitrary.
* `--token-file TOKEN_FILE`: Same usage as in `clone.py`.
* `--current-membership`: Prints the current group memberships according to git.uwaterloo.ca and quit. The memberships are printed by project
   and by student ID.
* `--check-membership`: Checks the CSV file and the groups that are already on git.uwaterloo.ca. Checks that:
   * Students are in only one group on Gitlab and in the CSV file.
   * Each group in the CSV file has 1 to 3 members.
   * If a student's group in the CSV file is different from their group on Gitlab, the script will tell you.

#### Examples:

1. `./stqam-create-repos.py --current-membership --token-file ~/.gitlab_token_cs447 stqam-2017 cs447_groups1.csv`

   Prints out which students are in what group. The output is sorted by project name and then by student ID.
   Quits after printing the information (no projects are created).

1. `./stqam-create-repos.py --check-membership --token-file ~/.gitlab_token_cs447 stqam-2017 cs447_groups1.csv`

   Performs some checks on the groups on Gitlab and the CSV file. Reports any problems it finds. No new projects
   will be created.

1. `./stqam-create-repos.py --token-file ~/.gitlab_token_cs447 stqam-2017 cs447_groups1.csv`

   Reads your private Gitlab token from the file `~/.gitlab_token_cs447`. Then creates a project for each group in
   `cs447_groups1.csv` that doesn't have a number at the end. You can run the script with `--check-membership` argument
   before and after creating projects as a sanity check.

   
### `gitlab.py` and `ldap.py`

These files have some helper functions that are used by
other scripts. They don't do anything when run by themselves.
