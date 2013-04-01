Overview
--------

toggl-cli is a command-line interface for toggl.com.

It certainly does not implement the full toggl API, but rather those functions
that I use all the time. The goal is to make using toggl quicker and more
efficient for those already familiar with command-line tools.

toggl-cli is written in Python and uses version 6 of the toggl API.

This version of toggl-cli is forked from Dr. Robert Adams original toggl-cli
https://github.com/drobertadams/toggl-cli which uses a similar interface
to Todo.txt. This one has been modified to emulate Git and has additional
features not available in the original version.

Usage
-----
usage: toggl [-h] [-v] {ls,add,edit,now,proj,start,stop,www,rm} ...

positional arguments:
  {ls,add,edit,now,proj,start,stop,www,rm}
                        sub-command help
    ls                  List time entries
    add                 Add a new time entry
    edit                Edit an existing time entry
    now                 Show the current time entry
    proj                Show your project list
    start               Start a new time entry
    stop                Start a new time entry
    www                 Open the webpage
    rm                  Remove a time entry

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Enable verbose output

Additional options for each command can be accessed from the help
system by doing "toggl CMD -h" where CMD is one of the positional
arguments listed above.

Requirements
------------

* requests module
* pytz module
* dateutil module

Configuration
-------------

Move the example config to ~/.togglrc and edit appropriately, or run the
program which will generate a ~/.togglrc for editing.

Limitations
-----------

* When creating a time entry for a given project, the project must already
  exist.
* Clients, workspaces, project users, tasks, tags, and users aren't supported,
  simply because I don't use these features. I only use tasks and projects.
