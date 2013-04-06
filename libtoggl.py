import json
import requests
import urllib
try:
    from urllib.parse import quote as url_quote
except:
    from urllib import quote as url_quote

TOGGL_API_VERSION = 'v6'

KEY_ID          = 'id'
KEY_NAME        = 'name'
KEY_DESC        = 'description'
KEY_PROJECT     = 'project'
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
KEY_ESTSECS     = 'estimated_seconds'
KEY_TASK        = 'task'

class TogglRawData:
    def __init__(self):
        self._url = None
        self._reqdata = None
        self._respdata = None

    @property
    def request_url(self):
        return self._url

    @request_url.setter
    def request_url(self, value):
        self._url = value

    @property
    def request_data(self):
        return self._reqdata

    @request_data.setter
    def request_data(self, value):
        self._reqdata = value

    @property
    def response_data(self):
        return self._respdata

    @response_data.setter
    def response_data(self, value):
        self._respdata = value

class TogglApi:
    def __init__(self, url, auth, api_version=TOGGL_API_VERSION, verbose=False):
        self.base_url = '%s/%s' % (url, api_version)
        self.auth = auth
        self.verbose = verbose
        self.headers = {'content-type': 'application/json'}

    def _raise_if_error(self, r):
        if r.status_code != 200:
            print("Error reason: " + r.text)
        r.raise_for_status()

    def get_projects(self, raw_data=None):
        """Fetches the projects as JSON objects."""
        
        if raw_data is None or raw_data.response_data is None:
            url = "%s/projects.json" % self.base_url
            if self.verbose:
                print(url)
            r = requests.get(url, auth=self.auth)
            self._raise_if_error(r)

            if self.verbose:
                print(r.text)
            from_text = r.text

            if raw_data is not None:
                raw_data.request_url = url
                raw_data.response_data = from_text
        else:
            from_text = raw_data.response_data

        if (self.verbose):
            print(from_text)

        return [TogglProject(p) for p in json.loads(from_text)['data']]

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
        data = { KEY_PROJECT : proj.to_json() }

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

        data = {KEY_ID : projlist}

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

        data = {KEY_ID : projlist}

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

    def get_workspaces(self, raw_data=None):
        """Get the list of workspaces."""

        if raw_data is None or raw_data.response_data is None:
            url = "%s/workspaces.json" % self.base_url
            if self.verbose:
                print(url)
            r = requests.get(url, auth=self.auth)
            self._raise_if_error(r)
            
            from_text = r.text

            if raw_data is not None:
                raw_data.request_url = url
                raw_data.response_data = from_text
        else:
            from_text = raw_data.response_data

        if self.verbose:
            print(from_text)

        return [TogglWorkspace(w) for w in json.loads(from_text)['data']]

    def get_workspace_users(self, wsp_id):
        """Get the user list for the specified workspace."""
        url = "%s/workspaces/%s/users.json" % (self.base_url, wsp_id)
        if self.verbose:
            print(url)
        r = requests.get(url, auth=self.auth)
        self._raise_if_error(r)

        if self.verbose:
            print(r.text)

        return [TogglUser(u) for u in json.loads(r.text)['data']]

    def get_clients(self, raw_data=None):
        """Get list of clients."""
        if raw_data is None or raw_data.response_data is None:
            url = "%s/clients.json" % (self.base_url)
            if self.verbose:
                print(url)
            r = requests.get(url, auth=self.auth)
            self._raise_if_error(r)

            from_text = r.text

            if raw_data is not None:
                raw_data.request_url = url
                raw_data.response_data = from_text
        else:
            from_text = raw_data.response_data

        if self.verbose:
            print(from_text)

        return [TogglClient(c) for c in json.loads(from_text)['data']]

    def add_client(self, cl):
        """Add a new client entry."""
        url = "%s/clients.json" % (self.base_url)
        data = { KEY_CLIENT : cl.to_json() }

        if self.verbose:
            print(url)
            print(data)

        r = requests.post(url, auth=self.auth,
            data=json.dumps(data), headers=self.headers)
        self._raise_if_error(r)

        if self.verbose:
            print(r.text)

        return TogglResponse(True, json.loads(r.text))

    def update_client(self, cl):
        """Update an existing client entry."""
        url = "%s/clients/%d.json" % (self.base_url, cl.id)
        data = { KEY_CLIENT : cl.to_json() }

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

    def delete_client(self, client_id):
        """Delete the time entry with the specified id"""
        url = "%s/clients/%d.json" % (self.base_url, int(client_id))
        if self.verbose:
            print(url)
        r = requests.delete(url, auth=self.auth, data=None, headers=self.headers)
        if r.status_code == 404:
            return TogglResponse(False)
        self._raise_if_error(r)

        if self.verbose:
            print(r.text)

        return TogglResponse(True, json.loads(r.text))

    def get_tasks(self, active=True):
        """Get the list of tasks"""
        url = "%s/tasks.json?active=%s" % (self.base_url, active)
        if self.verbose:
            print(url)
        r = requests.get(url, auth=self.auth)
        self._raise_if_error(r)

        from_text = r.text

        if self.verbose:
            print(from_text)

        return [TogglTask(t) for t in json.loads(from_text)['data']]

    def add_task(self, task):
        """Add a new client entry."""
        url = "%s/tasks.json" % (self.base_url)
        data = { KEY_TASK: task.to_json() }

        if self.verbose:
            print(url)
            print(data)

        r = requests.post(url, auth=self.auth,
            data=json.dumps(data), headers=self.headers)
        self._raise_if_error(r)

        if self.verbose:
            print(r.text)

        return TogglResponse(True, json.loads(r.text))

    def delete_task(self, task_id):
        """Delete a task entry."""
        url = "%s/tasks/%d.json" % (self.base_url, int(task_id))

        if self.verbose:
            print(url)
        r = requests.delete(url, auth=self.auth, data=None, headers=self.headers)
        if r.status_code == 404:
            return TogglResponse(False)
        self._raise_if_error(r)

        if self.verbose:
            print(r.text)

        return TogglResponse(True, json.loads(r.text))

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

class TogglObject(object):
    def __init__(self, fields=None):
        if fields is not None:
            self.fields = fields
        else:
            self.fields = {}
            self.fields[KEY_ID] = None
            self.name = None

    @property
    def id(self):
        return self.fields[KEY_ID]

    @property
    def name(self):
        return self.fields[KEY_NAME]

    @name.setter
    def name(self, value):
        self.fields[KEY_NAME] = value

class TogglTask(TogglObject):
    def __init__(self, fields=None):
        TogglObject.__init__(self, fields)
        if fields is not None:
            if KEY_WORKSPACE in fields:
                self._workspace = TogglWorkspace(fields[KEY_WORKSPACE])
            else:
                self._workspace = None

    @property
    def workspace(self):
        return self._workspace

    @workspace.setter
    def workspace(self, value):
        self._workspace = value
        if self._workspace:
            self.fields[KEY_WORKSPACE] = self._workspace.to_json()

    @property
    def project(self):
        return self._project

    @project.setter
    def project(self, value):
        self._project = value
        if self._project:
            self.fields[KEY_PROJECT] = self._project.to_json()

    @property
    def user(self):
        return self._user

    @user.setter
    def user(self, value):
        self._user = value
        if self._user:
            self.fields[KEY_USER] = self._user.to_json()

    @property
    def estimated_workhours(self):
        return self.fields[KEY_ESTWKHRS]

    @estimated_workhours.setter
    def estimated_workhours(self, value):
        self.fields[KEY_ESTWKHRS] = value

    @property
    def estimated_seconds(self):
        return self.fields[KEY_ESTSECS]

    @estimated_seconds.setter
    def estimated_seconds(self, value):
        self.fields[KEY_ESTSECS] = value

    @property
    def is_active(self):
        return self.fields[KEY_ISACTIVE]

    @is_active.setter
    def is_active(self, value):
        self.fields[KEY_ISACTIVE] = value

    def to_json(self):
        return self.fields

class TogglWorkspace(TogglObject):
    def __init__(self, fields=None):
        TogglObject.__init__(self, fields)

    @property
    def profile_name(self):
        return self.fields[KEY_PROFILE]

    @property
    def is_admin(self):
        return self.fields[KEY_ISADMIN]

    def to_json(self):
        return self.fields

class TogglUser(TogglObject):
    def __init__(self, fields=None):
        TogglObject.__init__(self, fields)

    @property
    def fullname(self):
        return self.fields[KEY_FULLNAME]

    @property
    def email(self):
        return self.fields[KEY_EMAIL]

    def to_json(self):
        return self.fields

class TogglClient(TogglObject):
    def __init__(self, fields=None):
        TogglObject.__init__(self, fields)

        if fields is not None:
            if KEY_WORKSPACE in fields:
                self._workspace = TogglWorkspace(fields[KEY_WORKSPACE])
            else:
                self._workspace = None
        else:
            self._workspace = None
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

    @property
    def workspace(self):
        return self._workspace

    @workspace.setter
    def workspace(self, value):
        self._workspace = value
        if self._workspace:
            self.fields[KEY_WORKSPACE] = self._workspace.to_json()

    def to_json(self):
        return self.fields

class TogglProject(TogglObject):
    def __init__(self, fields=None):
        TogglObject.__init__(self, fields)
        if fields is not None:
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
        self.fields[KEY_ID] = value

    @property
    def workspace(self):
        return self._workspace

    @workspace.setter
    def workspace(self, value):
        self._workspace = value
        if self._workspace:
            self.fields[KEY_WORKSPACE] = self._workspace.to_json()

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
        return self.fields

class TogglEntry(object):
    def __init__(self, fields=None):
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
        self.ignore_start_and_stop = False
        self.fields[KEY_CREATEDW] = 'toggl-cli'

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
        if self._project:
            self.fields[KEY_PROJECT] = self._project.to_json()

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
        return self.fields
