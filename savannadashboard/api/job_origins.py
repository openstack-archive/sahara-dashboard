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


class JobOrigin(base.Resource):
    resource_name = 'Job Origin'
    defaults = {'description': ''}


class JobOriginManager(base.ResourceManager):
    resource_class = JobOrigin

    def create(self, name, storage_type, username, password,
               location, description):

        data = {
            'credentials': {'user': username,
                            'password': password
                            },
            'name': name,
            'description': description,
            'storage_type': storage_type,
            'url': location
        }
        self._create('/job-origins', data)

    def list(self):
        return self._list('/job-origins', 'job_origins')

    def get(self, job_origin_id):
        return self._get('/job-origins/%s' % job_origin_id,
                         'resource')

    def delete(self, job_origin_id):
        self._delete('/job-origins/%s' % job_origin_id)
