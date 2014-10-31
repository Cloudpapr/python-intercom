# coding=utf-8
#
# Copyright 2012 keyes.ie
#
# License: http://jkeyes.mit-license.org/
#
""" intercom module

All of the API requests are created, and the API responses are parsed here.

>>> from intercom import Intercom
>>> Intercom.app_id = 'dummy-app-id'
>>> Intercom.api_key = 'dummy-api-key'

"""

__version__ = '0.2.13.1'

import functools
import json
import numbers
import requests
import time

DEFAULT_TIMEOUT = 10  # seconds


class IntercomError(Exception):
    """ Base error. """
    def __init__(self, message, result=None):
        super(IntercomError, self).__init__(message)
        self.result = result


class AuthenticationError(IntercomError):
    """ Raised when a request cannot be authenticated by the API. """
    pass


class BadGatewayError(IntercomError):
    """ Raised when a request does not reach the API due to a 502. """
    pass


class ResourceNotFound(IntercomError):
    """ Raised when a resource cannot be found e.g. a non-existant User. """
    pass


class ServerError(IntercomError):
    """ Raised when the API returns an error other than an auth or not found.
    """
    pass


class ServiceUnavailableError(IntercomError):
    """ Raised when the API cannot be handle a request. """
    pass


class CustomData(dict):
    """ A dict that limits keys to strings, and values to real numbers
    and strings.

    >>> from intercom.company import CustomData
    >>> data = CustomData()
    >>> data['a_dict'] = {}
    Traceback (most recent call last):
        ...
    ValueError: custom data only allows string and real number values
    >>> data[1] = "a string"
    Traceback (most recent call last):
        ...
    ValueError: custom data only allows string keys

    """

    def __setitem__(self, key, value):
        """ Limits the keys and values. """
        if not (
            isinstance(value, numbers.Real) or
            isinstance(value, basestring)
        ):
            raise ValueError(
                "custom data only allows string and real number values")
        if not isinstance(key, basestring):
            raise ValueError("custom data only allows string keys")
        super(CustomData, self).__setitem__(key, value)


def api_call(func_to_decorate):
    """ Decorator for handling AWS credentials. """
    @functools.wraps(func_to_decorate)
    def wrapper(*args, **kwargs):
        """ Decorator closure. """
        response = func_to_decorate(*args, **kwargs)
        raise_errors_on_failure(response)
        if not response.content.strip():
            return ''
        result = json.loads(response.content)
        return result
    return wrapper


def raise_errors_on_failure(response):
    if response.status_code == 400:
        raise ServerError("Bad Request – General client error, possibly malformed data.")
    elif response.status_code == 404:
        raise ResourceNotFound("Not found.")
    elif response.status_code == 401:
        raise AuthenticationError("Invalid API key/username provided.")
    elif response.status_code == 402:
        raise ServerError("Payment Required – The API is not available on your current plan.")
    elif response.status_code == 403:
        raise ServerError("Forbidden – The request is not allowed.")
    elif response.status_code == 404:
        raise ServerError("Not Found – The resource was not found.")
    elif response.status_code == 405:
        raise ServerError("Method Not Allowed – The resource does not accept the HTTP method.")
    elif response.status_code == 406:
        raise ServerError("Not Acceptable – The resource cannot return the client’s required content type.")
    elif response.status_code == 408:
        raise ServerError("Request Timeout – The server would not wait any longer for the client.")
    elif response.status_code == 409:
        raise ServerError("Conflict - the client is trying to update with a stale version or data.")
    elif response.status_code == 415:
        raise ServerError("Unsupported Media Type - The server doesn’t accept the submitted content-type.")
    elif response.status_code == 422:
        raise ServerError("Unprocessable Entity – The data was well-formed but invalid.")
    elif response.status_code == 429:
        raise ServerError("Too Many Requests – The client has reached or exceeded a rate limit, or the server is overloaded.")
    elif response.status_code == 500:
        raise ServerError("Server error.")
    elif response.status_code == 502:
        raise BadGatewayError("Bad gateway.")
    elif response.status_code == 503:
        raise ServiceUnavailableError("Service unavailable.")
    elif response.status_code == 504:
        raise ServiceUnavailableError("Service unavailable.")


class Intercom(object):
    """ Intercom API Wrapper """

    app_id = None
    api_key = None
    api_version = 1
    api_endpoint = 'https://api.intercom.io/v' + str(api_version) + '/'
    api_endpoint = 'https://api.intercom.io/'
    timeout = DEFAULT_TIMEOUT

    @classmethod
    @api_call
    def _call(cls, method, url, params=None):
        """ Construct an API request, send it to the API, and parse the
        response. """
        req_params = {}
        headers = {
            'User-Agent': 'python-intercom/' + __version__,
            'Accept': 'application/json'
        }
        if method in ('POST', 'PUT', 'DELETE'):
            headers['content-type'] = 'application/json'
            req_params['data'] = json.dumps(params)
        elif method == 'GET':
            req_params['params'] = params
        req_params['headers'] = headers

        resp = requests.request(
            method, url, timeout=Intercom.timeout,
            auth=(Intercom.app_id, Intercom.api_key), **req_params)
        return resp

    @classmethod
    def _create_or_update_user(cls, method, **kwargs):
        """ Used by create_user and update_user. """
        user_dict = Intercom._call(
            method, Intercom.api_endpoint + 'users', params=kwargs)
        return user_dict

    @classmethod
    def _create_or_update_company(cls, method, **kwargs):
        """ Used by create_company and update_company. """
        company_dict = Intercom._call(
            method, Intercom.api_endpoint + 'companies', params=kwargs)
        return company_dict

    @classmethod
    def get_users(cls, **kwargs):
        """ Returns a paginated list of all users in your application on
        Intercom.

        **Arguments**

        * ``page``: optional (defaults to 1)
        * ``per_page``: optional (defaults to 500, max value of 500)
        * ``tag_id``: optional — query for users that are tagged with a
          specific tag.
        * ``tag_name``: optional — query for users that are tagged with a
          specific tag.

        **Response**

        * ``users``: an array of User objects (same as returned by getting a
          single User)
        * ``total_count``: the total number of Users tracked in your Intercom
          application
        * ``page``: the current requested page
        * ``next_page``: the next page number, if any
        * ``previous_page``: the previous page number, if any
        * ``total_pages``: the total number of pages

        >>> result = Intercom.get_users()
        >>> type(result)
        <type 'dict'>
        >>> len(result['users'])
        3

        """
        return Intercom._call(
            'GET', Intercom.api_endpoint + 'users', params=kwargs)

    @classmethod
    def get_companies(cls, **kwargs):
        """ Returns a paginated list of all companies in your application on
        Intercom.

        **Arguments**

        * ``page``: optional - what page of results to fetch (defaults to first page)
        * ``per_page``: optional - how many results per page (defaults to 50)
        * ``order``: optional - asc or desc. Return the companies in ascending or descending order. (defaults to desc)

        **Response**

        * ``type``: value is ‘company.list’
          single User)
        * ``total_count``: The number of companies for this App
        * ``companies``: A list of companies
        * ``pages``: Optional. A pagination object, which may be empty, indicating no further pages to fetch


        >>> result = Intercom.get_companies()
        >>> type(result)
        <type 'dict'>
        >>> len(result['companies'])
        3

        """
        return Intercom._call(
            'GET', Intercom.api_endpoint + 'companies', params=kwargs)

    @classmethod
    def get_user(cls, email=None, user_id=None):
        """ Return a dict for the user represented by the specified email
        or user_id.

        >>> user = Intercom.get_user(user_id='123')
        >>> user['name']
        u'Somebody'

        """

        params = {'email': email, 'user_id': user_id}
        user_dict = Intercom._call(
            'GET', Intercom.api_endpoint + 'users', params=params)
        return user_dict

    @classmethod
    def get_company(cls, name=None, company_id=None):
        """ Return a dict for the company represented by the specified name
        or company_id.

        >>> company = Intercom.get_company(company_id='123')
        >>> company['name']
        u'Somebody'

        """

        params = {'name': name, 'company_id': company_id}
        company_dict = Intercom._call(
            'GET', Intercom.api_endpoint + 'companies', params=params)
        return company_dict

    @classmethod
    def create_user(cls, **kwargs):
        """ Creates a user.

        N.B. Social and geo location data is fetched asynchronously, so a
        secondary call to users will be required to fetch it.

        **Arguments**

        - ``user_id``: required (if no email) — a unique string identifier
          for the user
        - ``email``: required (if no user_id) — the user's email address
        - ``name``: The user's full name
        - ``created_at``: A UNIX timestamp representing the date the user was
          created
        - ``custom_data``: A hash of key/value pairs containing any other data
          about the user you want Intercom to store.
        - ``last_seen_ip``: An ip address (e.g. "1.2.3.4") representing the
          last ip address the user visited your application from. (Used for
          updating location_data)
        - ``last_seen_user_agent``: The user agent the user last visited your
          application with.
        - ``companies``: An array of hashes describing the companies this user
          belongs to. Currently companies are not returned in the response.
        - ``last_request_at or last_impression_at``: A UNIX timestamp
          representing the date the user last visited your application.
        - ``unsubscribed_from_emails``: A boolean value representing the users
          unsubscribed status.


        >>> user = Intercom.create_user(user_id='7902',
        ... email='ben@intercom.io',
        ... name='Somebody', created_at=1270000000, last_seen_ip='1.2.3.4',
        ... custom_data={ 'app_name': 'Genesis'}, last_request_at=1300000000)
        >>> user['name']
        u'Somebody'
        >>> user['custom_data']['app_name']
        u'Genesis'
        >>> user['last_impression_at']
        1300000000

        """
        return Intercom._create_or_update_user('POST', **kwargs)

    @classmethod
    def create_company(cls, **kwargs):
        """ Creates a company.

        **Arguments**

        - ``company_id``: The company id you have defined for the company
        - ``remote_created_at``: optional - The time the company was created by you
        - ``name``: The name of the company
        - ``monthly_spend``: How much revenue the company generates for your business
        - ``plan``: The name of the plan you have associated with the company
        - ``session_count``: How many sessions the company has recorded
        - ``custom_attributes``: A hash of key/value pairs containing any other data about 
            the company you want Intercom to store


        >>> company = Intercom.create_company(company_id='123',
        ... name='My company', custom_data={ 'category': 'Premium'})
        >>> company['name']
        u'My company'
        >>> user['custom_data']['category']
        u'Premium'

        """
        return Intercom._create_or_update_company('POST', **kwargs)

    @classmethod
    def update_user(cls, **kwargs):
        """ Update a user with the available parameters.

        >>> user = Intercom.get_user(user_id='123')
        >>> user['name']
        u'Somebody'
        >>> user = Intercom.update_user(user_id='123', name='Guido')
        >>> user['name']
        u'Guido'

        """
        return Intercom._create_or_update_user('POST', **kwargs)

    @classmethod
    def update_company(cls, **kwargs):
        """ Update a company with the available parameters.

        >>> company = Intercom.get_user(company_id='123')
        >>> company['name']
        u'My company'
        >>> company = Intercom.update_user(company_id='123', name='My new company')
        >>> company['name']
        u'My new company'

        """
        return Intercom._create_or_update_company('POST', **kwargs)

    @classmethod
    def delete_user(cls, user_id=None, email=None):
        """ Delete a user.

        >>> user = Intercom.get_user(user_id='123')
        >>> user['email']
        u'somebody@example.com'

        """
        params = {
            'email': email,
            'user_id': user_id
        }
        user_dict = Intercom._call(
            'DELETE', Intercom.api_endpoint + 'users', params)
        return user_dict

    @classmethod
    def create_impression(
            cls, user_id=None, email=None, user_ip=None,
            user_agent=None, location=None):
        """ Create an impression.

        >>> result = Intercom.create_impression(email="somebody@example.com",
        ... user_agent="MyApp/1.0", user_ip="2.3.4.5")
        >>> result['unread_messages']
        1

        """
        params = {
            'email': email,
            'user_id': user_id,
            'user_ip': user_ip,
            'user_agent': user_agent,
            'location': location
        }
        user_dict = Intercom._call(
            'POST', Intercom.api_endpoint + 'users/impressions', params=params)
        return user_dict

    @classmethod
    def create_note(cls, user_id=None, email=None, body=None):
        """ Create a note.

        >>> result = Intercom.create_note(email="somebody@example.com",
        ... body="This is a note")
        >>> result['html']
        u'<p>This is a note</p>'
        >>> result['user']['email']
        u'somebody@example.com'

        """
        params = {
            'email': email,
            'user_id': user_id,
            'body': body
        }
        user_dict = Intercom._call(
            'POST', Intercom.api_endpoint + 'users/notes', params=params)
        return user_dict

    @classmethod
    def get_message_threads(cls, user_id=None, email=None, thread_id=None):
        """ If a thread_id is specified, this returns a specific MessageThread
        (if it can find one), otherwise it returns all MessageThreads for the
        particular user.

        >>> message_threads = Intercom.get_message_threads(
        ... email="somebody@example.com")
        >>> type(message_threads)
        <type 'list'>
        >>> message_thread = Intercom.get_message_threads(
        ... email="somebody@example.com", thread_id=5591)
        >>> type(message_thread)
        <type 'dict'>

        """
        params = {
            'email': email,
            'user_id': user_id,
            'thread_id': thread_id
        }
        msg_dict = Intercom._call(
            'GET', Intercom.api_endpoint + 'users/message_threads',
            params=params)
        return msg_dict

    @classmethod
    def create_message_thread(cls, user_id=None, email=None, body=None):
        """ Create a MessageThread.

        >>> message_thread = Intercom.create_message_thread(
        ... email="somebody@example.com",
        ... body="Hey Intercom, What is up?")
        >>> message_thread['thread_id']
        5591
        >>> len(message_thread['messages'])
        3
        >>> message_thread['messages'][0]['html']
        u'<p>Hey Intercom, What is up?</p>\n\n<p></p>'

        """
        params = {
            'email': email,
            'user_id': user_id,
            'body': body
        }
        user_dict = Intercom._call(
            'POST', Intercom.api_endpoint + 'users/message_threads',
            params=params)
        return user_dict

    @classmethod
    def reply_message_thread(
            cls, user_id=None, email=None, thread_id=None, body=None,
            read=None):
        """ Reply to the specific thread.

        >>> message_thread = Intercom.reply_message_thread(
        ... email="somebody@example.com",
        ... thread_id=5591,
        ... body="If you're not talking to me you must be talking to someone")
        >>> len(message_thread)
        9
        >>> message_thread['thread_id']
        5591
        >>> len(message_thread['messages'])
        3

        """
        params = {
            'email': email,
            'user_id': user_id,
            'thread_id': thread_id,
            'body': body,
            'read': read
        }
        user_dict = Intercom._call(
            'PUT', Intercom.api_endpoint + 'users/message_threads',
            params=params)
        return user_dict

    @classmethod
    def create_tag(
            cls, name, tag_or_untag, user_ids=None, emails=None):
        """ Create a tag (and maybe tag users).

        >>> tag = Intercom.create_tag("Free Trial", "tag",
        ... user_ids=["abc123", "def456"])
        >>> tag['id'] != None
        True
        >>> tag['name']
        u'Free Trial'
        >>> tag['tagged_user_count']
        2

        """

        params = {
            'name': name,
            'tag_or_untag': tag_or_untag,
            'user_ids': user_ids,
            'emails': emails
        }
        tag_dict = Intercom._call(
            'POST', Intercom.api_endpoint + 'tags', params=params)
        return tag_dict

    @classmethod
    def update_tag(
            cls, name, tag_or_untag, user_ids=None, emails=None):
        """ Update a tag (and maybe tag users).

        >>> tag = Intercom.update_tag("Free Trial", "tag",
        ... user_ids=["abc123", "def456"])
        >>> tag['id'] != None
        True
        >>> tag['name']
        u'Free Trial'
        >>> tag['tagged_user_count']
        2

        """

        params = {
            'name': name,
            'tag_or_untag': tag_or_untag,
            'user_ids': user_ids,
            'emails': emails
        }
        tag_dict = Intercom._call(
            'PUT', Intercom.api_endpoint + 'tags', params=params)
        return tag_dict

    @classmethod
    def get_tag(cls, name=None):
        """ Return a dict for the tag by the specified name.

        >>> tag = Intercom.get_tag(name="Free Trial")
        >>> tag['id'] != None
        True
        >>> tag['name']
        u'Free Trial'
        >>> tag['tagged_user_count']
        2

        """

        params = {'name': name}
        tag_dict = Intercom._call(
            'GET', Intercom.api_endpoint + 'tags', params=params)
        return tag_dict

    @classmethod
    def create_event(cls, event_name=None, user_id=None, email=None, metadata=None):
        """
        Create an event
        """
        params = {
            'event_name': event_name,
            'user_id': user_id,
            'email': email,
            'created': int(time.time()) 
         }

        if isinstance(metadata, dict):
            params['metadata'] = metadata

        call = Intercom._call(
             'POST', Intercom.api_endpoint + 'events', params=params)
        return call
