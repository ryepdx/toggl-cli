import json
import requests
import urllib
try:
    from urllib.parse import quote as url_quote
except:
    from urllib import quote as url_quote

KEY_ID          = 'id'
KEY_NAME        = 'name'
KEY_DESC        = 'description'
KEY_PROJ        = 'project'
KEY_START       = 'start'
KEY_STOP        = 'stop'
KEY_DURATION    = 'duration'
KEY_PROFILE     = 'profile_name'
KEY_ISADMIN     = 'current_user_is_admin'
KEY_FULLNAME    = 'fullname'
KEY_EMAIL       = 'email'

class TogglApi:
    def __init__(self, url, auth, verbose=False):
        self.base_url = url
        self.auth = auth
        self.verbose = verbose
        self.headers = {'content-type': 'application/json'}

    def get_projects(self):
        """Fetches the projects as JSON objects."""
        
        url = "%s/projects.json" % self.base_url
        if self.verbose:
            print(url)
        r = requests.get(url, auth=self.auth)
        r.raise_for_status() # raise exception on error

        if self.verbose:
            print(r.text)

        return [TogglProject(p) for p in json.loads(r.text)['data']]

    def get_time_entries(self, start=None, end=None):
        """Get the list of entries for the specified time range,
        or the latest entries if no dates specified"""
        # Fetch the data or die trying.
        # Toggle has the start/end dates creating a confusing
        # backwards range. Swap them here.
        url = "%s/time_entries.json" % self.base_url
        if start is not None and end is not None:
            url = "%s?start_date=%s&end_date=%s" % \
                    (url, url_quote(str(end)), url_quote(str(start)))
        if self.verbose:
            print(url)
        r = requests.get(url, auth=self.auth)
        r.raise_for_status() # raise exception on error

        if self.verbose:
            print(r.text)

        return [TogglEntry(e) for e in json.loads(r.text)['data']]

    def get_time_entry(self, entry_id):
        """Find the entry with the specified id"""
        # Fetch the data or die trying.
        # Toggle has the start/end dates creating a confusing
        # backwards range. Swap them here.
        url = "%s/time_entries/%s.json" % \
            (self.base_url, url_quote(entry_id))
        if self.verbose:
            print(url)
        r = requests.get(url, auth=self.auth)
        if r.status_code == 404:
            return None 
        r.raise_for_status() # raise exception on error
        
        if self.verbose:
            print(r.text)

        return TogglEntry(json.loads(r.text)['data'])

    def add_time_entry(self, entry):
        """Add the given entry as a new time entry"""
        data = entry.to_json()
        url = "%s/time_entries.json" % self.base_url
        if self.verbose:
            print(url)
        r = requests.post(url, auth=self.auth,
            data=json.dumps(data), headers=self.headers)
        r.raise_for_status() # raise exception on error
        
        if self.verbose:
            print(r.text)

        return TogglResponse(True, json.loads(r.text))

    def update_time_entry(self, entry):
        """Update the given time entry"""
        data = entry.to_json()
        url = "%s/time_entries/%d.json" % (self.base_url, entry.id)
        if self.verbose:
            print(url)
        r = requests.put(url, auth=self.auth, data=json.dumps(data), headers=self.headers)
        if r.status_code == 404:
            return TogglResponse(False)
        r.raise_for_status() # raise exception on error

        if self.verbose:
            print(r.text)

        return TogglResponse(True, json.loads(r.text))

    def delete_time_entry(self, entry_id):
        """Delete the time entry with the specified id"""
        url = "%s/time_entries/%s.json" % (self.base_url, url_quote(entry_id))
        if self.verbose:
            print(url)
        r = requests.delete(url, auth=self.auth, data=None, headers=self.headers)
        if r.status_code == 404:
            return TogglResponse(False)
        r.raise_for_status() # raise exception on error

        if self.verbose:
            print(r.text)

        return TogglResponse(True, json.loads(r.text))

    def get_workspaces(self):
        url = "%s/workspaces.json" % self.base_url
        if self.verbose:
            print(url)
        r = requests.get(url, auth=self.auth)
        r.raise_for_status() # raise exception on error
        
        if self.verbose:
            print(r.text)

        return [TogglWorkspace(w) for w in json.loads(r.text)['data']]

    def get_workspace_users(self, wsp_id):
        url = "%s/workspaces/%s/users.json" % (self.base_url, wsp_id)
        if self.verbose:
            print(url)
        r = requests.get(url, auth=self.auth)
        r.raise_for_status() # raise exception on error

        if self.verbose:
            print(r.text)

        return [TogglUser(u) for u in json.loads(r.text)['data']]

class TogglResponse:
    def __init__(self, success, data=None):
        self._success = success
        self._data = data

    @property
    def success(self):
        return self._success

    @property
    def data(self):
        return self._data['data']

class TogglWorkspace:
    def __init__(self, fields):
        self.fields = fields

    @property
    def id(self):
        return self.fields[KEY_ID]

    @property
    def profile_name(self):
        return self.fields[KEY_PROFILE]

    @property
    def name(self):
        return self.fields[KEY_NAME]

    @property
    def is_admin(self):
        return self.fields[KEY_ISADMIN]

class TogglUser:
    def __init__(self, fields):
        self.fields = fields

    @property
    def fullname(self):
        return self.fields[KEY_FULLNAME]

    @property
    def email(self):
        return self.fields[KEY_EMAIL]

class TogglProject:
    def __init__(self, fields=None):
        if fields is not None:
            self.fields = fields
        else:
            self.fields = {}
            self.name = ''
            self.id = ''

    @property
    def name(self):
        return self.fields[KEY_NAME]

    @name.setter
    def name(self, value):
        self.fields[KEY_NAME] = value

    @property
    def id(self):
        return self.fields[KEY_ID]

    @id.setter
    def id(self, value):
        self.fields[KEY_PROJID] = value

    def to_json(self):
        return {
                 KEY_ID : self.id,
                 KEY_NAME : self.name
               }

class TogglEntry:
    def __init__(self, fields=None):
        self.ignore_times = False
        if fields is not None:
            self.fields = fields
            if KEY_PROJ in fields:
                self.project = TogglProject(fields['project'])
            else:
                self.project = None
        else:
            self.fields = {}
            self.id = ''
            self.desc = ''
            self.project = None
            self.start_time = ''
            self.stop_time = ''
            self.duration = ''

    @property
    def ignore_start_and_stop(self):
        return self.ignore_times

    @ignore_start_and_stop.setter
    def ignore_start_and_stop(self, value):
        self.ignore_times = value

    @property
    def id(self):
        return self.fields[KEY_ID]

    @id.setter
    def id(self, value):
        self.fields[KEY_ID] = value

    @property
    def desc(self):
        return self.fields[KEY_DESC]

    @desc.setter
    def desc(self, value):
        self.fields[KEY_DESC] = value

    @property
    def project(self):
        return self._project

    @project.setter
    def project(self, value):
        self._project = value

    @property
    def start_time(self):
        return self.fields[KEY_START]

    @start_time.setter
    def start_time(self, value):
        self.fields[KEY_START] = value

    @property
    def stop_time(self):
        return self.fields[KEY_STOP]

    @stop_time.setter
    def stop_time(self, value):
        self.fields[KEY_STOP] = value

    @property
    def duration(self):
        return self.fields[KEY_DURATION]

    @duration.setter
    def duration(self, value):
        self.fields[KEY_DURATION] = value

    def to_json(self):
        """Creates a basic time entry JSON from the current entry
           project_name should not have the '@' prefix.
           duration should be an integer seconds.
        """
        
        # Create JSON object to send to toggl.
        data = { 'time_entry' : \
            { 'duration' : self.duration,
              'billable' : False,
              'start' : self.start_time,
              'description' : self.desc,
              'created_with' : 'toggl-cli',
              'ignore_start_and_stop' : self.ignore_start_and_stop 
            }
        }
        if self.stop_time != None:
            data['time_entry']['stop'] = self.stop_time
        if self.project != None:
            data['time_entry']['project'] = self.project.to_json()
        
        return data
