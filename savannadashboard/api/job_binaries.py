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


class JobBinary(base.Resource):
    resource_name = 'Job Binary'
    defaults = {}


class JobBinaryManager(base.ResourceManager):
    resource_class = JobBinary

    def create(self, name, url, description, extra):
        data = {
            "name": name,
            "url": url,
            "description": description,
            "extra": extra
        }

        return self._create('/job-binaries', data)

    def list(self):
        return self._list('/job-binaries', 'binaries')

    def get(self, job_binary_id):
        return self._get('/job-binaries/%s' % job_binary_id,
                         'resource')

    def delete(self, job_binary_id):
        self._delete('/job-binaries/%s' % job_binary_id)
