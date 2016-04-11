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

You can save the output of the scripts (or any program really) using [tee](https://en.wikipedia.org/wiki/Tee_%28command%29).
For example, you can run `./clone.py cs123-spring2016 | tee clone-ouput.txt`.

All scripts accept `-h` and `--help` arguments and will print a help message. You may have to make the scripts
executable before running them (for example, which `chmod 700`). More documentation is below.

### `clone.py`

The `clone.py` script is used to clone the students' repositories.

#### Arguments:

* `group_name`: The only mandatory argument is the group name. The group name can be found from the
  Gitlab [Groups page](https://git.uwaterloo.ca/dashboard/groups). Course staff, including TAs, should
  be added to the group as owners using the web interface.
* `--url-type {http,ssh,http-save,ssh-save}`: You can choose to use either `http` or `ssh` for the repository
  URL. The default is `http`. To setup `ssh`, see the Gitlab doc on [SSH keys](https://git.uwaterloo.ca/help/ssh/README).
  If you are cloning many repositories, typing in your credentials every time is exhausting. You can make `clone.py` remember
  your credentials using the `-save` versions. For `http-save`, your credentials will be saved for 30 minutes in memory with
  the command:
  
  `git config --global credential.helper 'cache --timeout=1800'`

  For `ssh-save`, your passphrase is saved using `ssh-agent` and `ssh-add`.
* `--token-file TOKEN_FILE`: Access to Gitlab is needed to get all the projects in the group. You can
  find your private token from Gitlab [Account page](https://git.uwaterloo.ca/profile/account). By default, you'll
  be asked to type it in (won't be echo'ed back). If you don't want to keep typing in the token, save the token in
  the first line of a file by itself, then set `TOKEN_FILE` to a path to the file.
* `--clone-dir CLONE_DIR`: Will clone the students' repositories into the folder `CLONE_DIR`. The default is `./group_name/`,
  ie a folder with the same name as `group_name` in the current directory.
* `--revert-to-date REVERT_TO_DATE`: This option will pull from master branch and checkout the last revision before `REVERT_TO_DATE`.
  If you already cloned the repos (ex. by running `clone.py` previously), you can still use this option to update your copy to whatever
  the student has in the master branch before the due date. The format of `REVERT_TO_DATE` is `YYYY-MM-DD hh:mm:ss` (ex. `2016-05-20 15:30:00`).
  If this option isn't given, the script will just clone.
* `--students STUDENTS`: The default is to clone (and possibly revert) all the repositories in the given group. Use this option if you only want to 
  perform these actions on a select set of students. `STUDENTS` should be a comma separated list of student Quest IDs.
  
#### Examples:

1. `./clone.py cs123-spring2016 --url-type http-save`

    Clones all the repositories in the group cs123-spring2016 to the folder `./cs123-spring2016`.
    You'll be asked to type in your private token and your Gitlab credentials once. The only git
    command that will be run is `git clone`. You might run this near the start of term to clone
    all the students' repos.

1. `./clone.py cs123-spring2016 --token-file ~/.gitlab_token --url-type http-save`

    Same as above, except that the private token will be read from the first line of ~/.gitlab_token, a
    text file you have to created manually.

1. `./clone.py cs123-spring2016 --url-type ssh-save --revert-to-date '2016-05-30 13:00:00' --students j4ansmith,yralimonl,t2yang`

    Clones the repositories for three students j4ansmith, yralimonl, and t2yang. If the directory to clone to already exists,
    git will throw an error (this can happen if you cloned previously, in which case you can ignore the error).
    The script will then pull master and revert to the last revision before 1:00pm on May 30, 2016.

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
        $ ./batch-operation.py cs349-test1/ pwd
        /u5/yc2lee/gitlab-assignments/cs349-test1/cscf-t01
        /u5/yc2lee/gitlab-assignments/cs349-test1/cscf-t02
        /u5/yc2lee/gitlab-assignments/cs349-test1/cscf-t03
        /u5/yc2lee/gitlab-assignments/cs349-test1/cscf-t04
        /u5/yc2lee/gitlab-assignments/cs349-test1/cscf-t05
        /u5/yc2lee/gitlab-assignments/cs349-test1/random-project
        $

1. This example will pass the folder name to `echo Hello,` and print an informative header.

        $ ./batch-operation.py --headers --pass-name cs349-test1 'echo Hello,'
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

        $ ./batch-operation.py --headers cs349-test1/ 'git log -1 --oneline'
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
