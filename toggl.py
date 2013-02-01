#!/usr/bin/env python2
"""
toggl.py

Created by Robert Adams on 2012-04-19.
Last modified: Thu May 24, 2012 08:37PM

Modified by Morgan Howe (mthowe@gmail.com)
Last modified: Fri Sep 14, 2012

Copyright (c) 2012 D. Robert Adams. All rights reserved.
"""

#############################################################################
### Configuration Section                                                 ###
###

# How do you log into toggl.com?
AUTH = ('', '')

# Do you want to ignore starting times by default?
IGNORE_START_TIMES = False

# Command to visit toggl.com
WWW_ADDRESS = "open http://www.toggl.com"

###                                                                       ###
### End of Configuration Section                                          ###
#############################################################################

import datetime
import iso8601
import json
import os
import pytz
import requests
import sys
import time
import urllib
import ConfigParser
import argparse
from dateutil.parser import *

TOGGL_URL = "https://www.toggl.com/api/v6"
DEFAULT_DATEFMT = '%Y-%m-%d (%A)'
DEFAULT_ENTRY_DATEFMT = '%Y-%m-%d %H:%M%p'

def add_time_entry(args):
    """
    Creates a completed time entry.
    args should be: ENTRY [@PROJECT] DURATION
    """
    
    fields = {}

    fields['description'] = args.msg
    
    if args.proj is not None:
        fields['project'] = find_project(args.proj)['id']
    else:
        fields['project'] = None
    
    # Start and end params
    if args.start is not None:
        fields['start_time'] = parse_time_str(args.start)
    else:
        fields['start_time'] = datetime.datetime.utcnow().isoformat()

    if args.end is not None:
        fields['end_time'] = parse_time_str(args.end)
    else:
        fields['end_time'] = datetime.datetime.utcnow().isoformat()

    # Get the duration.
    if args.duration is not None:
        fields['duration'] = parse_duration(args.duration)
    else:
        start_time = iso8601.parse_date(fields['start_time']).astimezone(pytz.utc)
        end_time = iso8601.parse_date(parse_time_str(fields['end_time'])).astimezone(pytz.utc)

        fields['duration'] = (end_time - start_time).seconds
    
    # Create the JSON object, or die trying.
    data = create_time_entry_json(fields)
    if data == None:
        return 1
    
    if args.duration is not None:
        data['ignore_start_and_stop'] = True
    else:
        data['ignore_start_and_stop'] = False

    if args.verbose:
        print json.dumps(data)
    
    # Send the data.
    headers = {'content-type': 'application/json'}
    r = requests.post("%s/time_entries.json" % TOGGL_URL, auth=AUTH,
        data=json.dumps(data), headers=headers)
    r.raise_for_status() # raise exception on error
    
    return 0

def edit_time_entry(args):
    """Update an existing time entry"""

    if args.verbose:
        print(args)
    # Get an array of objects of recent time data.
    upd_entry = get_time_entry(args.id)["data"]

    if args.verbose:
        print json.dumps(upd_entry)

    fields = {}

    if args.proj != None:
        fields['project'] = find_project(args.proj)['id']
    else:
        fields['project'] = upd_entry['project']['id']

    if args.msg != None:
        fields['description'] = args.msg
    else:
        fields['description'] = upd_entry['description']

    if args.start != None:
        fields['start_time'] = parse_time_str(args.start)
    else:
        fields['start_time'] = upd_entry['start']

    if args.end != None:
        fields['end_time'] = parse_time_str(args.end)
    else:
        fields['end_time'] = upd_entry['stop']

    if args.calc_duration != False:
        start_time = iso8601.parse_date(fields['start_time']).astimezone(pytz.utc)
        end_time = iso8601.parse_date(parse_time_str(fields['end_time'])).astimezone(pytz.utc)

        fields['duration'] = (end_time - start_time).seconds
    else:
        if args.duration != None:
            fields['duration'] = parse_duration(args.duration)
        else:
            fields['duration'] = upd_entry['duration']

    new_ent = create_time_entry_json(fields)

    url = "%s/time_entries/%s.json" % (TOGGL_URL, urllib.quote(args.id))

    if args.verbose:
        print url

    headers = {'content-type': 'application/json'}
    r = requests.put(url, auth=AUTH, data=json.dumps(new_ent), headers=headers)
    r.raise_for_status() # raise exception on error

    return 0
            
def parse_time_str(timestr):
    tz = pytz.timezone(toggl_cfg.get('options', 'timezone'))
    tmp = parse(timestr)
    if tmp.tzinfo is None:
        tmp = tz.localize(tmp)
    return tmp.astimezone(pytz.utc).isoformat()

def create_time_entry_json(fields):
    """Creates a basic time entry JSON from the given arguments
       project_name should not have the '@' prefix.
       duration should be an integer seconds.
    """
    
    duration = fields['duration']
    start_time = fields['start_time']
    end_time = fields['end_time']
    project_id = fields['project']

    # Create JSON object to send to toggl.
    data = { 'time_entry' : \
        { 'duration' : fields['duration'],
          'billable' : False,
          'start' : start_time,
          'stop' : end_time,
          'description' : fields['description'],
          'created_with' : 'toggl-cli',
          'ignore_start_and_stop' : IGNORE_START_TIMES 
        }
    }
    if project_id != None:
        data['time_entry']['project'] = { 'id' : project_id }
    
    return data

def elapsed_time(seconds, suffixes=['y','w','d','h','m','s'], add_s=False, separator=' '):
    """
    Takes an amount of seconds and turns it into a human-readable amount of time.
    From http://snipplr.com/view.php?codeview&id=5713
    """
    # the formatted time string to be returned
    time = []

    # the pieces of time to iterate over (days, hours, minutes, etc)
    # - the first piece in each tuple is the suffix (d, h, w)
    # - the second piece is the length in seconds (a day is 60s * 60m * 24h)
    if toggl_cfg.has_option('options', 'use_mandays') and \
            toggl_cfg.getboolean('options', 'use_mandays') == True:

        parts = [('md', 60 * 60 * 8),
              (suffixes[3], 60 * 60),
              (suffixes[4], 60),
              (suffixes[5], 1)]
    else:
        parts = [(suffixes[0], 60 * 60 * 24 * 7 * 52),
              (suffixes[1], 60 * 60 * 24 * 7),
              (suffixes[2], 60 * 60 * 24),
              (suffixes[3], 60 * 60),
              (suffixes[4], 60),
              (suffixes[5], 1)]
    
    # for each time piece, grab the value and remaining seconds, and add it to
    # the time string
    for suffix, length in parts:
        value = seconds / length
        if value > 0:
            seconds = seconds % length
            time.append('%s%s' % (str(value),
                           (suffix, (suffix, suffix + 's')[value > 1])[add_s]))
        if seconds < 1:
            break
    
    return separator.join(time)

def get_current_time_entry():
    """Returns the current time entry JSON object, or None."""
    response = get_time_entries()
    
    for entry in response['data']:
        if int(entry['duration']) < 0:
            return entry
    
    return None

def get_projects():
    """Fetches the projects as JSON objects."""
    
    url = "%s/projects.json" % TOGGL_URL
    if args.verbose:
        print url
    r = requests.get(url, auth=AUTH)
    r.raise_for_status() # raise exception on error
    return json.loads(r.text)

def get_time_entry(entry_id):
    # Fetch the data or die trying.
    # Toggle has the start/end dates creating a confusing
    # backwards range. Swap them here.
    url = "%s/time_entries/%s.json" % \
        (TOGGL_URL, urllib.quote(entry_id))
    if args.verbose:
        print url
    r = requests.get(url, auth=AUTH)
    r.raise_for_status() # raise exception on error
    
    return json.loads(r.text)

def get_time_entries(start=None, end=None):
    """Fetches time entry data and returns it as a Python array."""
    
    tz = pytz.timezone(toggl_cfg.get('options', 'timezone'))

    end_date = None
    # Construct the start and end dates. Toggl seems to want these in UTC.
    if start != None:
        lt = tz.localize(parse(args.start))
        end_date = lt.astimezone(pytz.utc)
    else:
        endday = datetime.datetime.now(pytz.utc)
        # Set the default start day to monday
        if endday.weekday() != 0:
            endday = endday - datetime.timedelta(days=endday.weekday())
        end_date = tz.localize(datetime.datetime(endday.year, endday.month, endday.day, 0, 0, 0))
 
    start_date = None
    # The end date is actually earlier in time than start date
    if end != None:
        lt = tz.localize(parse(args.end))
        start_date = lt.astimezone(pytz.utc)
    else:
        today = datetime.datetime.now()
        start_date = today.replace(hour=23, minute=59, second=59)
    
    # Fetch the data or die trying.
    # Toggle has the start/end dates creating a confusing
    # backwards range. Swap them here.
    url = "%s/time_entries.json?start_date=%s&end_date=%s" % \
        (TOGGL_URL, urllib.quote(str(end_date)), urllib.quote(str(start_date)))
    if args.verbose:
        print url
    r = requests.get(url, auth=AUTH)
    r.raise_for_status() # raise exception on error
    
    return json.loads(r.text)

def list_current_time_entry(args):
    """Shows what the user is currently working on (duration is negative)."""
    entry = get_current_time_entry()
    if entry != None:
        print_time_entry(entry)
    else:
        print "You're not working on anything right now."
    
    return 0

def list_projects(args):
    """List all projects."""
    response = get_projects()
    for project in response['data']:
        print "@%s" % project['name']
    return 0

def find_project(proj):
    """Find a project given the unique prefix of the name"""
    response = get_projects()
    for project in response['data']:
        if project['name'].startswith(proj):
            return project
    print "Could not find project!"
    sys.exit(1)

def list_time_entries_date(response):
    date_fmt = DEFAULT_DATEFMT
    if toggl_cfg.has_option('options', 'datefmt'):
        date_fmt = toggl_cfg.get('options', 'datefmt')

    # Sort the time entries into buckets based on "Month Day" of the entry.
    days = { }
    for entry in response['data']:
        tz = pytz.timezone(toggl_cfg.get('options', 'timezone'))
        start_time = iso8601.parse_date(entry['start']).astimezone(tz).strftime(date_fmt)
        if start_time not in days:
            days[start_time] = []
        days[start_time].append(entry)

    dur_sum = 0
    # For each day, print the entries, then sum the times.
    for date_str in sorted(days.keys()):
        print date_str

        duration = 0
        for entry in days[date_str]:
            print "  ",
            duration += print_time_entry(entry, verbose=args.verbose_list)
        print "   (%s)" % elapsed_time(int(duration))
        dur_sum += duration

    if args.sum:
        print "Total time: %s" % elapsed_time(dur_sum)
    return 0

def list_time_entries_project(response):
    projs = { }
    for entry in response['data']:
        if not 'project' in entry:
            proj = '(No Project)'
        else:
            proj = entry["project"]['name']
        if proj not in projs:
            projs[proj] = []
        projs[proj].append(entry)
    
    dur_sum = 0
    for proj in projs.keys():
        print "@" + proj
        duration = 0
        for entry in projs[proj]:
            print "  ",
            duration += print_time_entry(entry, show_proj=False, verbose=args.verbose_list)
        print "   (%s)" % (elapsed_time(int(duration)))
        dur_sum += duration

    if args.sum:
        print "Total time: %s" % elapsed_time(dur_sum)
    return 0

def list_time_entries(args):
    """Lists all of the time entries from yesterday and today along with
       the amount of time devoted to each.
    """

    # Get an array of objects of recent time data.
    response = get_time_entries(start=args.start, end=args.end)
    if args.verbose:
        print(args)
        print(response)

    if args.proj:
        list_time_entries_project(response)
    else:
        list_time_entries_date(response)

def parse_duration(str):
    """Parses a string of the form [[Hours:]Minutes:]Seconds and returns
       the total time in seconds as an integer.
    """
    elements = str.split(':')
    duration = 0
    if len(elements) == 3:
        duration += int(elements[0]) * 3600
        elements = elements[1:]
    if len(elements) == 2:
        duration += int(elements[0]) * 60
        elements = elements[1:]
    duration += int(elements[0])
    
    return duration
        
def print_time_entry(entry, show_proj=True, verbose=False):
    """Utility function to print a time entry object and returns the
       integer duration for this entry."""
    
    # If the duration is negative, the entry is currently running so we
    # have to calculate the duration by adding the current time.
    is_running = ''
    e_time = 0
    if entry['duration'] >= 0:
        e_time = int(entry['duration'])
    else:
        is_running = '* '
        e_time = (datetime.datetime.now(pytz.utc) - iso8601.parse_date(entry['start']).astimezone(pytz.utc)).seconds
    e_time_str = " %s" % elapsed_time(int(e_time), separator='')
    
    # Get the project name (if one exists).
    tz = pytz.timezone(toggl_cfg.get('options', 'timezone'))
    project_name = ''
    if not 'project' in entry:
        project_name = " (No Project)"
    elif show_proj:
        project_name = " @%s" % entry['project']['name']
    else:
        start_time = iso8601.parse_date(entry['start']).astimezone(tz)
        project_name = " %s" % start_time.date()

    if verbose:
        date_fmt = DEFAULT_ENTRY_DATEFMT
        if toggl_cfg.has_option('options', 'entry_datefmt'):
            date_fmt = toggl_cfg.get('options', 'entry_datefmt')

        st = iso8601.parse_date(entry['start']).astimezone(tz).strftime(date_fmt)
        if entry['stop'] == None:
            et = ""
        else:
            et = iso8601.parse_date(entry['stop']).astimezone(tz).strftime(date_fmt)

        print "[%s] %s%s%s%s (%s - %s)" % (entry['id'], is_running, entry['description'], \
                project_name, e_time_str, st, et)
    else:
        print "%s%s%s%s" % (is_running, entry['description'], project_name, e_time_str)

    return e_time

def delete_time_entry(args):
    entry_id = args.id

    response = get_time_entries()

    for entry in response['data']:
        if str(entry['id']) == entry_id:
            print "Deleting entry " + entry_id

            headers = {'content-type': 'application/json'}
            r = requests.delete("%s/time_entries/%s.json" % (TOGGL_URL, entry_id), auth=AUTH,
                data=None, headers=headers)
            r.raise_for_status() # raise exception on error

    return 0

def start_time_entry(args):
    """
       Starts a new time entry.
       args should be: ENTRY [@PROJECT]
    """
    
    entry = args.msg
    
    # See if we have a @project.
    project_id = None
    if args.proj is not None:
        project_id = find_project(args.proj)['id']

    fields = {}
    fields['description'] = args.msg
    fields['project'] = project_id
    start_time = None
    if args.time != None:
        start_time = parse_time_str(args.time)
    else:
        start_time = datetime.datetime.utcnow().isoformat()

    fields['start_time'] = start_time
    fields['end_time'] = None
    fields['duration'] = -1

    # Create JSON object to send to toggl.
    data = create_time_entry_json(fields)

    if args.verbose:
        print json.dumps(data)
    
    headers = {'content-type': 'application/json'}
    r = requests.post("%s/time_entries.json" % TOGGL_URL, auth=AUTH,
        data=json.dumps(data), headers=headers)
    r.raise_for_status() # raise exception on error
    
    return 0

def stop_time_entry(args):
    """Stops the current time entry (duration is negative)."""

    entry = get_current_time_entry()
    if entry != None:
        # Get the start time from the entry, converted to UTC.
        start_time = iso8601.parse_date(entry['start']).astimezone(pytz.utc)

        if args.time:
            tz = pytz.timezone(toggl_cfg.get('options', 'timezone'))
            stop_time = tz.localize(parse(args.time)).astimezone(pytz.utc)
        else:
            # Get stop time(now) in UTC.
            stop_time = datetime.datetime.now(pytz.utc)

        # Create the payload.
        data = { 'time_entry' : entry }
        data['time_entry']['stop'] = stop_time.isoformat()
        data['time_entry']['duration'] = (stop_time - start_time).seconds

        url = "%s/time_entries/%d.json" % (TOGGL_URL, entry['id'])

        if args.verbose:
            print url

        headers = {'content-type': 'application/json'}
        r = requests.put(url, auth=AUTH, data=json.dumps(data), headers=headers)
        r.raise_for_status() # raise exception on error
    else:
        print >> sys.stderr, "You're not working on anything right now."
        return 1

    return 0

def visit_web(args):
    if not toggl_cfg.has_option('options', 'web_browser_cmd'):
        print("Please set the web_browser_cmd setting in the options section of your ~/.togglrc")
    else:
        os.system(toggl_cfg.get('options', 'web_browser_cmd') + ' ' + WWW_ADDRESS)

def create_default_cfg():
    cfg = ConfigParser.RawConfigParser()
    cfg.add_section('auth')
    cfg.set('auth', 'username', 'user@example.com')
    cfg.set('auth', 'password', 'secretpasswd')
    cfg.add_section('options')
    cfg.set('options', 'ignore_start_times', 'False')
    cfg.set('options', 'timezone', 'UTC')
    cfg.set('options', 'web_browser_cmd', 'w3m')
    cfg.set('options', 'datefmt', DEFAULT_DATEFMT)
    cfg.set('options', 'entry_datefmt', DEFAULT_ENTRY_DATEFMT)
    cfg.set('options', 'use_mandays', False)
    with open(os.path.expanduser('~/.togglrc'), 'w') as cfgfile:
        cfg.write(cfgfile)

def main():
    """Program entry point."""
    
    global toggl_cfg
    toggl_cfg = ConfigParser.ConfigParser()
    if toggl_cfg.read(os.path.expanduser('~/.togglrc')) == []:
        create_default_cfg()
        print "Missing ~/.togglrc. A default has been created for editing."
        return 1

    global AUTH, IGNORE_START_TIMES
    AUTH = (toggl_cfg.get('auth', 'username').strip(), toggl_cfg.get('auth', 'password').strip())
    IGNORE_START_TIMES = toggl_cfg.getboolean('options', 'ignore_start_times')

    parser = argparse.ArgumentParser(prog='toggl')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')

    subparsers = parser.add_subparsers(help='sub-command help')

    parser_ls = subparsers.add_parser('ls', help='List time entries')
    parser_ls.add_argument('-p', '--proj', help='Sort entries by project', action='store_true', default=False)
    parser_ls.add_argument('-s', '--start', help='Specify start date', default=None)
    parser_ls.add_argument('-e', '--end', help='Specify end date', default=None)
    parser_ls.add_argument('-v', '--verbose-list', help='Show verbose output', action='store_true', default=False)
    parser_ls.add_argument('-S', '--sum', help='Show time summary', action='store_true', default=False)
    parser_ls.set_defaults(func=list_time_entries)

    parser_add = subparsers.add_parser('add', help='Add a new time entry')
    parser_add.add_argument('-m', '--msg', help='Log entry message', required=True)
    parser_add.add_argument('-p', '--proj', help='Project for the log entry')
    parser_add.add_argument('-s', '--start', help='Specify start date', default=None)
    parser_add.add_argument('-e', '--end', help='Specify end date', default=None)
    parser_add.add_argument('-d', '--duration', help='Entry duration', required=False)
    parser_add.set_defaults(func=add_time_entry)

    parser_edit = subparsers.add_parser('edit', help='Edit an existing time entry')
    parser_edit.add_argument('-i', '--id', help='The id to edit', required=True)
    parser_edit.add_argument('-m', '--msg', help='Log entry message')
    parser_edit.add_argument('-p', '--proj', help='Project for the log entry')
    parser_edit.add_argument('-d', '--duration', help='Entry duration')
    parser_edit.add_argument('-s', '--start', help='Specify start date', default=None)
    parser_edit.add_argument('-e', '--end', help='Specify end date', default=None)
    parser_edit.add_argument('-c', '--calc-duration', help='Calculate duration from start/end dates', action='store_true', default=False)
    parser_edit.set_defaults(func=edit_time_entry)

    parser_now = subparsers.add_parser('now', help='Show the current time entry')
    parser_now.set_defaults(func=list_current_time_entry)

    parser_proj = subparsers.add_parser('proj', help='Show your project list')
    parser_proj.set_defaults(func=list_projects)

    parser_start = subparsers.add_parser('start', help='Start a new time entry')
    parser_start.add_argument('-m', '--msg', help='Log entry message', required=True)
    parser_start.add_argument('-p', '--proj', help='Project for the log entry')
    parser_start.add_argument('-t', '--time', help='Specify the start date and/or time')
    parser_start.set_defaults(func=start_time_entry)

    parser_stop = subparsers.add_parser('stop', help='Start a new time entry')
    parser_stop.add_argument('-t', '--time', help='Specify the stop time')
    parser_stop.set_defaults(func=stop_time_entry)

    parser_www = subparsers.add_parser('www', help='Open the webpage')
    parser_www.set_defaults(func=visit_web)

    parser_rm = subparsers.add_parser('rm', help='Remove a time entry')
    parser_rm.add_argument('-i', '--id', help='The id to remove', required=True)
    parser_rm.set_defaults(func=delete_time_entry)

    global args
    args = parser.parse_args(sys.argv[1:])
    args.func(args)

if __name__ == "__main__":
    sys.exit(main())

# vim: set ts=4 sw=4 tw=0 :
