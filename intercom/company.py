# coding=utf-8
#
# Copyright 2012 keyes.ie
#
# License: http://jkeyes.mit-license.org/
#
""" Company module.

>>> from intercom import Intercom
>>> from intercom import Company

"""

from . import Intercom
from . import from_timestamp_property
from . import to_timestamp_property

from .intercom import CustomData


class CompanyId(dict):
    """ Base class for objects that required company_id and email properties. """

    @property
    def company_id(self):
        """ Returns the company_id. """
        return dict.get(self, 'company_id', None)

    @company_id.setter
    def company_id(self, company_id):
        """ Sets the company_id. """
        self['company_id'] = company_id

class Company(CompanyId):
    """ Object representing http://doc.intercom.io/api/?shell#companies).  """

    #attributes = (
    #    'type', 'created_at', 'remote_created_at', 'updated_at', 'company_id', 'name',
    #    'custom_attributes', 'session_count', 'monthly_spend', 'user_count', 'plan')

    attributes = ('company_id', 'name', 'plan', 'remote_created_at', 'monthly_spend', 'custom_attributes')

    @classmethod
    def find(cls, company_id=None, name=None):
        """ Find a user by company_id or name.

        >>> company = Company.find(name="My company")
        >>> user.company_id
        u'123'
        >>> company = Company.find(user_id=123)
        >>> company.name
        u'My company'

        """
        resp = Intercom.get_company(company_id=company_id, name=name)
        return cls(resp)

    @classmethod
    def create(cls, **kwargs):
        """ Create or update a company.

        >>> company = Company.create(name="My company")
        >>> company.name
        u'My company'

        """
        resp = Intercom.create_company(**kwargs)
        return cls(resp)

    @classmethod
    def all(cls):
        """ Return all of the Companies.

        >>> companies = Company.all()
        >>> len(companies)
        3
        >>> companies[0].name
        u'My company'

        """
        page = 1
        total_pages = 1
        companies = []
        while page <= total_pages:
            resp = Intercom.get_companies(page=page)
            page += 1
            total_pages = resp.get('total_pages', 0)
            companies.extend([cls(u) for u in resp['companies']])
        return companies

    def save(self):
        """ Creates or updates a Company.

        >>> company = Company()
        >>> company.name = "My company"
        >>> company.save()
        >>> company.name
        u'My company'

        """
        attrs = {}
        for key in Company.attributes:
            value = dict.get(self, key)
            if value is not None:
                attrs[key] = value
        resp = Intercom.update_company(**attrs)
        self.update(resp)

    @property
    def name(self):
        """ Returns the name of the company """
        return dict.get(self, 'name', None)

    @name.setter
    def name(self, name):
        """ Sets the name. """
        self['name'] = name

    @property
    def user_count(self):
        """ Returns the number of users in the company. """
        return dict.get(self, 'user_count', None)

    @property
    def session_count(self):
        """ Returns how many sessions the company has recorded. """
        return dict.get(self, 'session_count', 0)

    @property
    @from_timestamp_property
    def created_at(self):
        """ Returns the time the company was added to Intercom. """
        return dict.get(self, 'created_at', None)

    @property
    @from_timestamp_property
    def remote_created_at(self):
        """ Returns the time the company was created by you. """
        return dict.get(self, 'created_at', None)

    @created_at.setter
    @to_timestamp_property
    def remote_created_at(self, value):
        """ Sets the timestamp when the company was created by you. """
        self['remote_created_at'] = value

    @property
    def custom_data(self):
        """ Returns a CustomData object for this company.

        >>> companies = Company.all()
        >>> custom_data = companies[0].custom_data
        >>> type(custom_data)
        <class 'intercom.company.CustomData'>
        >>> custom_data['monthly_spend']
        155.5

        """
        data = dict.get(self, 'custom_data', None)
        if not isinstance(data, CustomData):
            data = CustomData(data)
            dict.__setitem__(self, 'custom_data', data)
        return data

    @custom_data.setter
    def custom_data(self, custom_data):
        """ Sets the CustomData for this company.

        >>> company = Company(company_id=123)
        >>> company.custom_data = { 'max_monthly_spend': 200 }
        >>> type(company.custom_data)
        <class 'intercom.company.CustomData'>
        >>> company.save()

        """
        if not isinstance(custom_data, CustomData):
            custom_data = CustomData(custom_data)
        self['custom_data'] = custom_data
