# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2013 Red Hat Inc.
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

from savannadashboard.api import base


class DataSource(base.Resource):
    resource_name = 'Data Source'
    defaults = {'description': ''}


class DataSourceManager(base.ResourceManager):
    resource_class = DataSource

    def create(self, name, description, data_source_type,
               url, credential_user, credential_pass):
        data = {
            'name': name,
            'description': description,
            'type': data_source_type,
            'url': url,
            'credentials': {'user': credential_user,
                            'password': credential_pass}
        }
        self._create('/data-sources', data)

    def list(self):
        return self._list('/data-sources', 'data_sources')

    def get(self, data_source_id):
        return self._get('/data-sources/%s' % data_source_id,
                         'resource')

    def delete(self, data_source_id):
        self._delete('/data-sources/%s' % data_source_id)
