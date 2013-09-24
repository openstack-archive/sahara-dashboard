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


class Job(base.Resource):
    resource_name = 'Job'
    defaults = {'description': ''}


class JobManager(base.ResourceManager):
    resource_class = Job

    def create(self, name, type, mains, libs, description):
        data = {
            'name': name,
            'type': type,
            'description': description,
            'mains': mains,
            'libs': libs  # TODO(croberts)fix when api is ready
        }

        self._create('/jobs', data)

    def list(self):
        return self._list('/jobs', 'jobs')

    def get(self, job_id):
        return self._get('/jobs/%s' % job_id, 'job')

    def delete(self, job_id):
        self._delete('/jobs/%s' % job_id)

    def launch(self, job_id, cluster_id, input_id, output_id, configs):
        url = "/jobs/%s/execute" % job_id
        data = {
            "input_id": input_id,
            "output_id": output_id,
            "cluster_id": cluster_id,
            "job_configs": configs
        }

        return self._create(url, data)
