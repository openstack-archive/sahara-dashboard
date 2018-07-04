# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from django.urls import reverse

from sahara_dashboard import api
from sahara_dashboard.test import helpers as test
from sahara_dashboard.test.helpers import IsHttpRequest


INDEX_URL = reverse('horizon:project:data_processing.jobs:index')
DETAILS_URL = reverse(
    'horizon:project:data_processing.jobs:details', args=['id'])


class DataProcessingJobTests(test.TestCase):

    @test.create_mocks({api.sahara: ('job_execution_list',
                                     'plugin_list', 'job_binary_list',
                                     'data_source_list',
                                     'job_list')})
    def test_index(self):
        self.mock_job_execution_list.return_value = \
            self.job_executions.list()

        res = self.client.get(INDEX_URL)
        self.mock_job_execution_list.assert_called_once_with(
            IsHttpRequest(), {})
        self.assertEqual(
            "cluster-1",
            (res.context_data["tab_group"]._tabs["jobs_tab"].
             _tables["jobs"].data[0].cluster_name))
        self.assertEqual(
            "job-1",
            (res.context_data["tab_group"]._tabs["jobs_tab"].
             _tables["jobs"].data[0].job_name))
        self.assertTemplateUsed(res, 'jobs/index.html')
        self.assertContains(res, 'Jobs')

    @test.create_mocks({api.sahara: ('job_execution_get',
                                     'cluster_get', 'job_get',
                                     'data_source_get')})
    def test_details(self):
        self.mock_job_execution_get.return_value = (
            self.job_executions.first())

        res = self.client.get(DETAILS_URL)
        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        self.assertContains(res, 'RUNNING')

    @test.create_mocks({api.sahara: ('job_execution_list',
                                     'job_execution_delete')})
    def test_delete(self):
        job_exec = self.job_executions.first()
        self.mock_job_execution_list.return_value = self.job_executions.list()
        self.mock_job_execution_delete.return_value = None

        form_data = {'action': 'jobs__delete__%s' % job_exec.id}
        res = self.client.post(INDEX_URL, form_data)
        self.mock_job_execution_list.assert_called_once_with(
            IsHttpRequest(), {})
        self.mock_job_execution_delete.assert_called_once_with(
            IsHttpRequest(), job_exec.id)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.assertMessageCount(success=1)
