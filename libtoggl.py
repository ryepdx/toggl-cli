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
KEY_PROJECT        = 'project'
KEY_START       = 'start'
KEY_STOP        = 'stop'
KEY_DURATION    = 'duration'
KEY_PROFILE     = 'profile_name'
KEY_ISADMIN     = 'current_user_is_admin'
KEY_FULLNAME    = 'fullname'
KEY_EMAIL       = 'email'
KEY_BILLABLE    = 'billable'
KEY_ESTWKHRS    = 'estimated_workhours'
KEY_AUTOCALCWH  = 'automatically_calculate_estimated_workhours'
KEY_HRLYRATE    = 'hourly_rate'
KEY_CURRENCY    = 'currency'
KEY_WORKSPACE   = 'workspace'
KEY_CLIENT      = 'client'
KEY_ISACTIVE    = 'is_active'
KEY_TIMEENTRY   = 'time_entry'
KEY_CREATEDW    = 'created_with'
KEY_IGNTIMES    = 'ignore_start_and_stop'

class TogglApi:
    def __init__(self, url, auth, verbose=False):
        self.base_url = url
        self.auth = auth
        self.verbose = verbose
        self.headers = {'content-type': 'application/json'}

    def _raise_if_error(self, r):
        if r.status_code != 200:
            print("Error reason: " + r.text)
        r.raise_for_status()

    def get_projects(self):
        """Fetches the projects as JSON objects."""
        
        url = "%s/projects.json" % self.base_url
        if self.verbose:
            print(url)
        r = requests.get(url, auth=self.auth)
        self._raise_if_error(r)

        if self.verbose:
            print(r.text)

        return [TogglProject(p) for p in json.loads(r.text)['data']]

    def add_project(self, proj):
        """Adds the given project as a new project."""

        url = "%s/projects.json" % self.base_url
        data = { KEY_PROJECT : proj.to_json() }

        if self.verbose:
            print(url)
            print(data)
        r = requests.post(url, auth=self.auth,
            data=json.dumps(data), headers=self.headers)
        self._raise_if_error(r)
        
        if self.verbose:
            print(r.text)

        return TogglResponse(True, json.loads(r.text))

    def update_project(self, proj):
        """Adds the given project as a new project."""

        url = "%s/projects/%s.json" % (self.base_url, url_quote(str(proj.id)))
        data = proj.to_json()

        if self.verbose:
            print(url)
            print(data)
        r = requests.put(url, auth=self.auth,
            data=json.dumps(data), headers=self.headers)
        self._raise_if_error(r)
        
        if self.verbose:
            print(r.text)

        return TogglResponse(True, json.loads(r.text))

    def archive_projects(self, projlist):
        """Archive the specified list of projects."""
        url = "%s/projects/archive.json" % (self.base_url)

        data = {'id' : projlist}

        if self.verbose:
            print(url)
            print(data)
        r = requests.put(url, auth=self.auth,
            data=json.dumps(data), headers=self.headers)
        self._raise_if_error(r)
        
        if self.verbose:
            print(r.text)

        return TogglResponse(True, json.loads(r.text))

    def reopen_projects(self, projlist):
        """Archive the specified list of projects."""
        url = "%s/projects/open.json" % (self.base_url)

        data = {'id' : projlist}

        if self.verbose:
            print(url)
            print(data)
        r = requests.put(url, auth=self.auth,
            data=json.dumps(data), headers=self.headers)
        self._raise_if_error(r)
        
        if self.verbose:
            print(r.text)

        return TogglResponse(True, json.loads(r.text))

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
        self._raise_if_error(r)

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
        self._raise_if_error(r)
        
        if self.verbose:
            print(r.text)

        return TogglEntry(json.loads(r.text)['data'])

    def add_time_entry(self, entry):
        """Add the given entry as a new time entry"""

        url = "%s/time_entries.json" % self.base_url
        data = { KEY_TIMEENTRY : entry.to_json() }

        if self.verbose:
            print(url)
            print(data)

        r = requests.post(url, auth=self.auth,
            data=json.dumps(data), headers=self.headers)
        self._raise_if_error(r)
        
        if self.verbose:
            print(r.text)

        return TogglResponse(True, json.loads(r.text))

    def update_time_entry(self, entry):
        """Update the given time entry"""
        url = "%s/time_entries/%d.json" % (self.base_url, entry.id)
        data = { KEY_TIMEENTRY : entry.to_json() }

        if self.verbose:
            print(url)
            print(data)

        r = requests.put(url, auth=self.auth, data=json.dumps(data), headers=self.headers)
        if r.status_code == 404:
            return TogglResponse(False)
        self._raise_if_error(r)

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
        self._raise_if_error(r)

        if self.verbose:
            print(r.text)

        return TogglResponse(True, json.loads(r.text))

    def get_workspaces(self):
        url = "%s/workspaces.json" % self.base_url
        if self.verbose:
            print(url)
        r = requests.get(url, auth=self.auth)
        self._raise_if_error(r)
        
        if self.verbose:
            print(r.text)

        return [TogglWorkspace(w) for w in json.loads(r.text)['data']]

    def get_workspace_users(self, wsp_id):
        url = "%s/workspaces/%s/users.json" % (self.base_url, wsp_id)
        if self.verbose:
            print(url)
        r = requests.get(url, auth=self.auth)
        self._raise_if_error(r)

        if self.verbose:
            print(r.text)

        return [TogglUser(u) for u in json.loads(r.text)['data']]

    def get_clients(self):
        url = "%s/clients.json" % (self.base_url)
        if self.verbose:
            print(url)
        r = requests.get(url, auth=self.auth)
        self._raise_if_error(r)

        if self.verbose:
            print(r.text)

        return [TogglClient(c) for c in json.loads(r.text)['data']]

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

class TogglObject:
    def __init__(self, fields):
        self.fields = fields

    @property
    def id(self):
        return self.fields[KEY_ID]

    @property
    def name(self):
        return self.fields[KEY_NAME]

    @name.setter
    def name(self, value):
        self.fields[KEY_NAME] = value

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

    def to_json(self):
        return {
                 KEY_ID : self.id,
                 KEY_NAME : self.name
               }

class TogglUser:
    def __init__(self, fields):
        self.fields = fields

    @property
    def fullname(self):
        return self.fields[KEY_FULLNAME]

    @property
    def email(self):
        return self.fields[KEY_EMAIL]

class TogglClient(TogglObject):
    def __init__(self, fields=None):
        TogglObject.__init__(self, fields)
        if fields is not None:
            self.fields = fields
        else:
            self.fields = {}
            self.hourly_rate = None
            self.currency = None

    @property
    def hourly_rate(self):
        return self.fields[KEY_HRLYRATE]

    @hourly_rate.setter
    def hourly_rate(self, value):
        self.fields[KEY_HRLYRATE] = value

    @property
    def currency(self):
        return self.fields[KEY_CURRENCY]

    @currency.setter
    def currency(self, value):
        self.fields[KEY_CURRENCY] = value

    def to_json(self):
        return {
                    KEY_ID : self.id,
                    KEY_NAME : self.name,
                    KEY_HRLYRATE : self.hourly_rate,
                    KEY_CURRENCY : self.currency,
               }

class TogglProject:
    def __init__(self, fields=None):
        if fields is not None:
            self.fields = fields
            if KEY_WORKSPACE in fields:
                self._workspace = TogglWorkspace(fields[KEY_WORKSPACE])
            else:
                self._workspace = None
            if KEY_CLIENT in fields:
                self._client = TogglClient(fields[KEY_CLIENT])
            else:
                self._client = None
        else:
            self._workspace = None
            self._client = None
            self.fields = {}
            self.id = None
            self.name = None
            self.billable = None
            self.estimated_workhours = None
            self.autocalc_estimated_workhours = None
            self.is_active = None

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

    @property
    def workspace(self):
        return self._workspace

    @workspace.setter
    def workspace(self, value):
        self._workspace = value

    @property
    def client(self):
        return self._client

    @client.setter
    def client(self, value):
        self._client = value

    @property
    def billable(self):
        return self.fields[KEY_BILLABLE]

    @billable.setter
    def billable(self, value):
        self.fields[KEY_BILLABLE] = value

    @property
    def estimated_workhours(self):
        return self.fields[KEY_ESTWKHRS]

    @estimated_workhours.setter
    def estimated_workhours(self, value):
        self.fields[KEY_ESTWKHRS] = value

    @property
    def autocalc_estimated_workhours(self):
        return self.fields[KEY_AUTOCALCWH]

    @autocalc_estimated_workhours.setter
    def autocalc_estimated_workhours(self, value):
        self.fields[KEY_AUTOCALCWH] = value

    @property
    def is_active(self):
        return self.fields[KEY_ISACTIVE]

    @is_active.setter
    def is_active(self, value):
        self.fields[KEY_ISACTIVE] = value

    def to_json(self):
        return {
                    KEY_ID : self.id,
                    KEY_NAME : self.name,
                    KEY_BILLABLE : self.billable,
                    KEY_ESTWKHRS : self.estimated_workhours,
                    # The api says this field is supported, but it always causes
                    # an internal server error. Ignore it for now.
                    #KEY_AUTOCALCWH : self.autocalc_estimated_workhours,
                    KEY_WORKSPACE : self.workspace.to_json(),
                    KEY_CLIENT : self.client.to_json() if self.client is not None else None,
                    KEY_ISACTIVE : self.is_active
               }

class TogglEntry:
    def __init__(self, fields=None):
        self.ignore_times = False
        if fields is not None:
            self.fields = fields
            if KEY_PROJECT in fields:
                self.project = TogglProject(fields[KEY_PROJECT])
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
        data = {
                KEY_DURATION : self.duration,
                KEY_BILLABLE : False,
                KEY_START : self.start_time,
                KEY_STOP : self.stop_time,
                KEY_DESC : self.desc,
                KEY_CREATEDW : 'toggl-cli',
                KEY_IGNTIMES : self.ignore_start_and_stop,
                KEY_PROJECT : self.project.to_json() if self.project is not None else None
               }
        
        return data
