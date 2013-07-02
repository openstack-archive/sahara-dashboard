# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2013 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import logging

LOG = logging.getLogger(__name__)


class Resource(object):
    resource_name = 'Something'
    defaults = {}

    def __init__(self, manager, info):
        self.manager = manager
        self._info = info
        self._set_defaults(info)
        self._add_details(info)

    def _set_defaults(self, info):
        for name, value in self.defaults.iteritems():
            if name not in info:
                info[name] = value

    def _add_details(self, info):
        for (k, v) in info.iteritems():
            try:
                setattr(self, k, v)
                self._info[k] = v
            except AttributeError:
                # In this case we already defined the attribute on the class
                pass

    def __str__(self):
        return '%s %s' % (self.resource_name, str(self._info))


def _check_item(obj, searches):
    try:
        return all(getattr(obj, attr) == value for (attr, value) in searches)
    except AttributeError:
        return False


class ResourceManager(object):
    resource_class = None

    def __init__(self, api):
        self.api = api

    def find(self, **kwargs):
        return [i for i in self.list() if _check_item(i, kwargs.items())]

    def _create(self, url, data):
        resp = self.api.client.post(url, json.dumps(data))

        if resp.status_code != 202:
            resource_name = self.resource_class.resource_name
            raise RuntimeError('Unable to create %s, server returned code %s' %
                               (resource_name, resp.status_code))

    def _update(self, url, data):
        resp = self.api.client.put(url, json.dumps(data))
        if resp.status_code != 202:
            resource_name = self.resource_class.resource_name
            raise RuntimeError('Unable to update %s, server returned code %s' %
                               (resource_name, resp.status_code))

    def _list(self, url, response_key):
        resp = self.api.client.get(url)

        if resp.status_code == 200:
            data = resp.json()[response_key]

            return [self.resource_class(self, res)
                    for res in data]
        else:
            plural_name = self._plurify_resource_name()
            raise RuntimeError('Unable to list %s, server returned code %s' %
                               (plural_name, resp.status_code))

    def _get(self, url, response_key=None):
        resp = self.api.client.get(url)

        if resp.status_code == 200:
            if response_key is not None:
                data = resp.json()[response_key]
            else:
                data = resp.json()
            return self.resource_class(self, data)
        else:
            resource_name = self.resource_class.resource_name
            raise RuntimeError('Unable to get %s, server returned code %s' %
                               (resource_name, resp.status_code))

    def _delete(self, url):
        resp = self.api.client.delete(url)

        if resp.status_code != 204:
            resource_name = self.resource_class.resource_name
            raise RuntimeError('Unable to delete %s, server returned code %s' %
                               (resource_name, resp.status_code))

    def _plurify_resource_name(self):
        return self.resource_class.resource_name + 's'


class APIException(Exception):
    pass
