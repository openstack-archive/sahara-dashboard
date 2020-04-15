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
    'horizon:project:data_processing.jobs:jb-details', args=['id'])
EDIT_URL = reverse('horizon:project:data_processing.jobs'
                   ':edit-job-binary', args=['id'])
CREATE_URL = reverse(
    'horizon:project:data_processing.jobs:create-job-binary')


class DataProcessingJobBinaryTests(test.TestCase):

    @test.create_mocks({api.sahara: ('job_execution_list',
                                     'plugin_list', 'job_binary_list',
                                     'data_source_list',
                                     'job_list')})
    def test_index(self):
        self.mock_job_binary_list.return_value = \
            self.job_binaries.list()
        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'jobs/index.html')
        self.assertContains(res, 'Job Binaries')
        self.assertContains(res, 'Name')
        self.assertContains(res, 'example.pig')
        self.mock_job_binary_list.assert_called_once_with(
            test.IsHttpRequest())

    @test.create_mocks({api.sahara: ('job_binary_get',)})
    def test_details(self):
        self.mock_job_binary_get.return_value = self.job_binaries.first()
        res = self.client.get(DETAILS_URL)
        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_job_binary_get, 2,
            mock.call(test.IsHttpRequest(), test.IsA(str)))

    @test.create_mocks({api.sahara: ('job_binary_list',
                                     'job_binary_get',
                                     'job_binary_internal_delete',
                                     'job_binary_delete',)})
    def test_delete(self):
        jb_list = self.mock_job_binary_list.return_value = \
            self.job_binaries.list()
        self.mock_job_binary_get.return_value = self.job_binaries.list()[0]
        self.mock_job_binary_delete.return_value = None
        int_id = jb_list[0].url.split("//")[1]
        self.mock_job_binary_internal_delete.return_value = None
        form_data = {"action": "job_binaries__delete__%s" % jb_list[0].id}
        res = self.client.post(INDEX_URL, form_data)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_job_binary_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_job_binary_get.assert_called_once_with(
            test.IsHttpRequest(), test.IsA(str))
        self.mock_job_binary_delete.assert_called_once_with(
            test.IsHttpRequest(), jb_list[0].id)
        self.mock_job_binary_internal_delete.assert_called_once_with(
            test.IsHttpRequest(), int_id)

    @test.create_mocks({api.sahara: ('job_binary_get',
                                     'job_binary_get_file')})
    def test_download(self):
        jb = self.mock_job_binary_get.return_value = \
            self.job_binaries.list()[0]
        self.mock_job_binary_get_file.return_value = \
            "TEST FILE CONTENT"

        context = {'job_binary_id': jb.id}
        url = reverse('horizon:project:data_processing.jobs:download',
                      kwargs={'job_binary_id': jb.id})
        res = self.client.get(url, context)
        self.assertTrue(res.has_header('content-disposition'))

        self.mock_job_binary_get.assert_called_once_with(
            test.IsHttpRequest(), test.IsA(str))
        self.mock_job_binary_get_file.assert_called_once_with(
            test.IsHttpRequest(), jb.id)

    @test.create_mocks({api.sahara: ('job_binary_get',
                                     'job_binary_get_file')})
    def test_download_with_spaces(self):
        jb = self.mock_job_binary_get.return_value = \
            self.job_binaries.list()[1]
        self.mock_job_binary_get_file.return_value = \
            "MORE TEST FILE CONTENT"

        context = {'job_binary_id': jb.id}
        url = reverse('horizon:project:data_processing.jobs:download',
                      kwargs={'job_binary_id': jb.id})
        res = self.client.get(url, context)
        self.assertEqual(
            res.get('Content-Disposition'),
            'attachment; filename="%s"' % jb.name
        )
        self.mock_job_binary_get.assert_called_once_with(
            test.IsHttpRequest(), test.IsA(str))
        self.mock_job_binary_get_file.assert_called_once_with(
            test.IsHttpRequest(), jb.id)

    @test.create_mocks({api.sahara: ('job_binary_get',
                                     'job_binary_update',
                                     'job_binary_internal_list')})
    def test_update(self):
        jb = self.mock_job_binary_get.return_value = \
            self.job_binaries.first()
        self.mock_job_binary_update.return_value = \
            self.job_binaries.first()

        form_data = {
            'job_binary_url': jb.url,
            'job_binary_name': jb.name,
            'job_binary_description': jb.description,
            'job_binary_type': "internal-db",
            'job_binary_internal': "",
            'job_binary_file': "",
            'job_binary_password': "",
            'job_binary_username': "",
            'job_binary_script': "",
            'job_binary_script_name': ""
        }
        res = self.client.post(EDIT_URL, form_data)
        self.assertNoFormErrors(res)
        self.mock_job_binary_get.assert_called_once_with(
            test.IsHttpRequest(), test.IsA(str))
        self.mock_job_binary_update.assert_called_once_with(
            test.IsHttpRequest(), test.IsA(str), test.IsA(dict))

    @test.create_mocks({api.manila: ('share_list', ),
                        api.sahara: ('job_binary_create',
                                     'job_binary_internal_list'),
                        api.sahara.base: ('is_service_enabled', )})
    def test_create_manila(self):
        share = mock.Mock()
        share.return_value = {"id": "tuvwxy56-1234-abcd-abcd-defabcdaedcb",
                              "name": "Test share"}
        shares = [share]
        self.mock_is_service_enabled.return_value = True
        self.mock_share_list.return_value = shares

        form_data = {
            "job_binary_type": "manila",
            "job_binary_manila_share": share.id,
            "job_binary_manila_path": "/testfile.bin",
            "job_binary_name": "testmanila",
            "job_binary_description": "Test manila description"
        }

        res = self.client.post(CREATE_URL, form_data)
        self.assertNoFormErrors(res)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_is_service_enabled, 1,
            mock.call(test.IsHttpRequest(), test.IsA(str)))

    @test.create_mocks({api.sahara: ('job_binary_create',
                                     'job_binary_internal_list')})
    def test_create_s3(self):
        form_data = {
            "job_binary_type": "s3",
            "job_binary_s3_url": "s3://a/b",
            "job_binary_access_key": "acc",
            "job_binary_secret_key": "sec",
            "job_binary_s3_endpoint": "http://pointy.end",
            "job_binary_name": "tests3",
            "job_binary_description": "Test s3 description"
        }
        res = self.client.post(CREATE_URL, form_data)
        self.assertNoFormErrors(res)
