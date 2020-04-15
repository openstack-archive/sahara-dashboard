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

from unittest import mock

from django.urls import reverse

from sahara_dashboard import api
from sahara_dashboard.test import helpers as test


INDEX_URL = reverse('horizon:project:data_processing.jobs:index')
DETAILS_URL = reverse(
    'horizon:project:data_processing.jobs:jt-details', args=['id'])


class DataProcessingJobTemplateTests(test.TestCase):

    @test.create_mocks({api.sahara: ('job_execution_list',
                                     'plugin_list', 'job_binary_list',
                                     'data_source_list',
                                     'job_list')})
    def test_index(self):
        self.mock_job_list.return_value = self.jobs.list()
        res = self.client.get(INDEX_URL)

        self.mock_job_list.assert_called_once_with(
            test.IsHttpRequest(), {})
        self.assertTemplateUsed(res, 'jobs/index.html')
        self.assertContains(res, 'Job Templates')
        self.assertContains(res, 'Name')
        self.assertContains(res, 'pigjob')

    @test.create_mocks({api.sahara: ('job_get',)})
    def test_details(self):
        self.mock_job_get.return_value = self.jobs.first()
        res = self.client.get(DETAILS_URL)

        self.mock_job_get.assert_called_with(
            test.IsHttpRequest(), 'id')
        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        self.assertContains(res, 'pigjob')
        self.assertContains(res, 'example.pig')
        self.assertContains(res, 'udf.jar')

    @test.create_mocks({api.sahara: ('job_binary_list',
                                     'job_create',
                                     'job_types_list')})
    def test_create(self):
        self.mock_job_binary_list.return_value = []
        self.mock_job_types_list.return_value = self.job_types.list()
        form_data = {'job_name': 'test',
                     'job_type': 'pig',
                     'lib_binaries': [],
                     'lib_ids': '[]',
                     'job_description': 'test create',
                     'hidden_arguments_field': [],
                     'argument_ids': '[]'}
        url = reverse('horizon:project:data_processing.jobs:create-job')
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_job_binary_list, 2,
            mock.call(test.IsHttpRequest()))
        self.mock_job_types_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_job_create.assert_called_once_with(
            test.IsHttpRequest(), 'test', 'Pig', [], [],
            'test create', interface=[], is_public=False,
            is_protected=False)

    @test.create_mocks({api.sahara: ('job_binary_list',
                                     'job_create',
                                     'job_types_list')})
    def test_create_with_interface(self):
        self.mock_job_binary_list.return_value = []
        self.mock_job_types_list.return_value = self.job_types.list()
        form_data = {'job_name': 'test_interface',
                     'job_type': 'pig',
                     'lib_binaries': [],
                     'lib_ids': '[]',
                     'job_description': 'test create',
                     'hidden_arguments_field': [],
                     'argument_ids': '["0", "1"]',
                     'argument_id_0': '0',
                     'argument_name_0': 'argument',
                     'argument_description_0': '',
                     'argument_mapping_type_0': 'args',
                     'argument_location_0': '0',
                     'argument_value_type_0': 'number',
                     'argument_required_0': True,
                     'argument_default_value_0': '',
                     'argument_id_1': '1',
                     'argument_name_1': 'config',
                     'argument_description_1': 'Really great config',
                     'argument_mapping_type_1': 'configs',
                     'argument_location_1': 'edp.important.config',
                     'argument_value_type_1': 'string',
                     'argument_default_value_1': 'A value'}
        url = reverse('horizon:project:data_processing.jobs:create-job')
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_job_binary_list, 2,
            mock.call(test.IsHttpRequest()))
        self.mock_job_types_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_job_create.assert_called_once_with(
            test.IsHttpRequest(),
            'test_interface', 'Pig', [], [], 'test create',
            interface=[
                {
                    "name": "argument",
                    "description": None,
                    "mapping_type": "args",
                    "location": "0",
                    "value_type": "number",
                    "required": True,
                    "default": None
                },
                {
                    "name": "config",
                    "description": "Really great config",
                    "mapping_type": "configs",
                    "location": "edp.important.config",
                    "value_type": "string",
                    "required": False,
                    "default": "A value"
                }],
            is_public=False,
            is_protected=False)

    @test.create_mocks({api.sahara: ('job_list',
                                     'job_delete')})
    def test_delete(self):
        job = self.jobs.first()
        self.mock_job_list.return_value = self.jobs.list()

        form_data = {'action': 'job_templates__delete__%s' % job.id}
        res = self.client.post(INDEX_URL, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.assertMessageCount(success=1)
        self.mock_job_list.assert_called_once_with(
            test.IsHttpRequest(), {})
        self.mock_job_delete.assert_called_once_with(
            test.IsHttpRequest(), job.id)

    @test.create_mocks({api.sahara: ('job_execution_create',
                                     'job_get',
                                     'job_get_configs',
                                     'job_list',
                                     'cluster_list',
                                     'data_source_list')})
    def test_launch(self):
        job = self.jobs.first()
        job_execution = self.job_executions.first()
        cluster = self.clusters.first()
        input_ds = self.data_sources.first()
        output_ds = self.data_sources.first()

        self.mock_job_get.return_value = job
        self.mock_job_get_configs.return_value = job
        self.mock_cluster_list.return_value = self.clusters.list()
        self.mock_data_source_list.return_value = self.data_sources.list()
        self.mock_job_list.return_value = self.jobs.list()
        self.mock_job_get.return_value = job
        self.mock_job_execution_create.return_value = job_execution

        url = reverse('horizon:project:data_processing.jobs:launch-job')
        form_data = {
            'job': self.jobs.first().id,
            'cluster': cluster.id,
            'job_input': input_ds.id,
            'job_output': output_ds.id,
            'config': {},
            'argument_ids': '{}',
            'adapt_oozie': 'on',
            'adapt_swift_spark': 'on',
            'hbase_common_lib': 'on',
            'hbase_common_lib': 'on',
            'datasource_substitute': 'on',
            'java_opts': '',
            'job_args_array': [[], []],
            'job_configs': [{}, {}],
            'job_params': [{}, {}],
            'job_type': 'Pig',
            'streaming_mapper': '',
            'streaming_reducer': ''
        }
        res = self.client.post(url, form_data)

        # there seem not to be an easy way to check the order
        # of the calls; check only if they happened
        self.assertNoFormErrors(res)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_job_get, 2,
            mock.call(test.IsHttpRequest(), job.id))
        self.mock_job_get_configs.assert_called_once_with(
            test.IsHttpRequest(), job.type)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_cluster_list, 2,
            mock.call(test.IsHttpRequest()))
        self.mock_data_source_list.assert_called_with(
            test.IsHttpRequest())
        self.mock_job_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_job_execution_create.assert_called_once_with(
            test.IsHttpRequest(),
            job.id,
            cluster.id,
            input_ds.id,
            output_ds.id,
            {
                'params': {},
                'args': [],
                'configs': {
                    'edp.substitute_data_source_for_name': True,
                    'edp.substitute_data_source_for_uuid': True}
            },
            {},
            is_public=False,
            is_protected=False)
